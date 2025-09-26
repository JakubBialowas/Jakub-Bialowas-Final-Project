import requests
import json
from datetime import datetime
from urllib.parse import urljoin
from typing import List, Dict, Optional, Any
import time

class GiosApi:
    """
    Klient do interakcji z GIOŚ REST API.
    """
    
    GIOS_API_BASE_URL = "https://api.gios.gov.pl/pjp-api/v1/rest/"

    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """
        Prywatna metoda pomocnicza do obsługi żądań API i błędów.
        """
        url = urljoin(self.GIOS_API_BASE_URL, endpoint)
        try:
            print(f"Making request to: {url}")  
            if params:
                print(f"With parameters: {params}")
            response = requests.get(url, params=params, timeout=30)  # Increased timeout for historical data
            response.raise_for_status()
            
            # Check if response is valid JSON
            try:
                data = response.json()
                print(f"API Response keys: {list(data.keys()) if isinstance(data, dict) else 'List with length: ' + str(len(data))}")  
                return data
            except json.JSONDecodeError:
                print(f"Invalid JSON response from API: {response.text[:200]}...")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Błąd połączenia z API GIOŚ: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error in API request: {e}")
            return None

    def get_stations(self) -> Optional[List[Dict[str, Any]]]:
        """Pobiera i normalizuje listę stacji pomiarowych."""

        data = self._make_request("station/findAll")
        if data is None:
            print("No data received from stations endpoint")
            return None

        # The public GIOŚ API returns a list with English keys. Some sandbox
        # environments provide a dictionary with Polish keys. Normalize both to
        # a common structure so the rest of the app can rely on it.
        normalized: List[Dict[str, Any]] = []

        if isinstance(data, list):
            source_iterable = data
        elif isinstance(data, dict) and 'Lista stacji pomiarowych' in data:
            source_iterable = data.get('Lista stacji pomiarowych') or []
        else:
            print(f"Unexpected stations response format: {type(data)}")
            if isinstance(data, dict):
                print(f"Available keys: {list(data.keys())}")
            return None

        for raw_station in source_iterable:
            if not isinstance(raw_station, dict):
                continue

            normalized.append(self._normalize_station(raw_station))

        print(f"Normalized {len(normalized)} stations from API response")
        return normalized

    @staticmethod
    def _normalize_station(raw_station: Dict[str, Any]) -> Dict[str, Any]:
        """Map API response (Polish or English keys) to a stable schema."""

        # English JSON structure (current public API)
        station_id = raw_station.get('id') or raw_station.get('stationId')
        station_name = raw_station.get('stationName') or raw_station.get('Nazwa stacji')
        lat = raw_station.get('gegrLat') or raw_station.get('Szerokość geograficzna')
        lon = raw_station.get('gegrLon') or raw_station.get('Długość geograficzna')
        street = raw_station.get('addressStreet') or raw_station.get('Ulica')

        # City information can be nested (English format) or flattened (Polish).
        city_block: Dict[str, Any] = {}
        if isinstance(raw_station.get('city'), dict):
            city_block = raw_station['city']
        else:
            city_block = {
                'id': raw_station.get('Identyfikator miasta'),
                'name': raw_station.get('Nazwa miasta'),
                'commune': {
                    'communeName': raw_station.get('Gmina'),
                    'districtName': raw_station.get('Powiat'),
                    'provinceName': raw_station.get('Województwo')
                }
            }

        return {
            'id': station_id,
            'stationName': station_name,
            'gegrLat': lat,
            'gegrLon': lon,
            'addressStreet': street,
            'city': {
                'id': (city_block or {}).get('id'),
                'name': (city_block or {}).get('name'),
                'commune': (city_block or {}).get('commune', {})
            }
        }

    def get_sensors_for_station(self, station_id: int) -> Optional[List[Dict[str, Any]]]:
        """
        Pobiera listę czujników dla danego ID stacji.
        Nowy format: Polskie nazwy pól
        """
        print(f"Fetching sensors for station {station_id}...")
        data = self._make_request(f"station/sensors/{station_id}")
        
        if data is None:
            return None
            
        # Handle the new Polish response format for sensors
        if isinstance(data, dict) and 'Lista stanowisk pomiarowych dla podanej stacji' in data:
            sensors_list = data['Lista stanowisk pomiarowych dla podanej stacji']
            if isinstance(sensors_list, list):
                print(f"Received {len(sensors_list)} sensors in new Polish format")
                
                # Convert to English-like format for compatibility
                converted_sensors = []
                for polish_sensor in sensors_list:
                    converted_sensor = {
                        'id': polish_sensor.get('Identyfikator stanowiska'),
                        'stationId': polish_sensor.get('Identyfikator stacji'),
                        'param': {
                            'paramName': polish_sensor.get('Wskaźnik', ''),
                            'paramFormula': polish_sensor.get('Wskaźnik - wzór', ''),
                            'paramCode': polish_sensor.get('Wskaźnik - kod', '')
                        },
                        'paramId': polish_sensor.get('Id wskaźnika')
                    }
                    converted_sensors.append(converted_sensor)
                
                return converted_sensors
        
        # Fallback to old format handling
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # Look for other possible keys
            possible_keys = ['sensors', 'data', 'values', 'result']
            for key in possible_keys:
                if key in data and isinstance(data[key], list):
                    return data[key]
        
        print(f"Unexpected sensors response format")
        if isinstance(data, dict):
            print(f"Available keys: {list(data.keys())}")
        return None

    def get_measurements_for_sensor(self, sensor_id: int, start_date: str = None, end_date: str = None) -> Optional[Dict[str, Any]]:
        """
        Pobiera dane pomiarowe dla danego ID czujnika z opcjonalnym zakresem dat.
        Automatycznie wybiera między danymi bieżącymi a historycznymi.
        """
        print("=" * 60)
        print(f"Requesting measurements for sensor {sensor_id}")
        
        if start_date and end_date:
            print(f"Historical data requested: {start_date} to {end_date}")
            # Try historical data first
            historical_data = self._get_historical_measurements(sensor_id, start_date, end_date)
            if historical_data and self._has_valid_measurements(historical_data):
                print("✓ Historical data found and valid")
                return historical_data
            else:
                print("✗ Historical data not available, falling back to recent data")
                # Fall back to recent data
                return self._get_recent_measurements(sensor_id)
        else:
            print("Recent data requested (default: last 3 days)")
            return self._get_recent_measurements(sensor_id)

    def _get_recent_measurements(self, sensor_id: int) -> Optional[Dict[str, Any]]:
        """
        Pobiera bieżące dane pomiarowe (ostatnia godzina do 3 dni wstecz).
        """
        endpoint = f"data/getData/{sensor_id}"
        print(f"Using recent data endpoint: {endpoint}")
        return self._make_request(endpoint)

    def _get_historical_measurements(self, sensor_id: int, start_date: str, end_date: str) -> Optional[Dict[str, Any]]:
        """
        Pobiera archiwalne dane pomiarowe.
        Próbuje różnych endpointów i parametrów dla danych historycznych.
        """
        print("Attempting to retrieve historical measurements...")
        
        # Lista możliwych endpointów dla danych historycznych
        historical_endpoints = [
            f"archival/data/{sensor_id}",
            f"data/archival/{sensor_id}", 
            f"historical/data/{sensor_id}",
            f"data/historical/{sensor_id}",
            f"data/getData/{sensor_id}",  # Standard endpoint z parametrami dat
        ]
        
        # Różne kombinacje parametrów dat
        param_combinations = [
            {'start': start_date, 'end': end_date},
            {'from': start_date, 'to': end_date},
            {'dateFrom': start_date, 'dateTo': end_date},
            {'startDate': start_date, 'endDate': end_date},
            {'period': f"{start_date}/{end_date}"},
        ]
        
        for endpoint in historical_endpoints:
            for params in param_combinations:
                print(f"Trying endpoint: {endpoint} with params: {params}")
                data = self._make_request(endpoint, params)
                
                if data and self._has_valid_measurements(data):
                    measurements = self._extract_measurements(data)
                    if measurements and self._is_historical_data(measurements, start_date, end_date):
                        print(f"✓ Valid historical data found using {endpoint}")
                        return data
                    elif measurements:
                        print(f"✗ Data found but not historical (wrong date range)")
                else:
                    print(f"✗ No valid data from {endpoint}")
                
                # Rate limiting - respect API limits
                time.sleep(0.5)
        
        print("No historical endpoint returned valid data")
        return None

    def _has_valid_measurements(self, data: Dict[str, Any]) -> bool:
        """
        Sprawdza czy odpowiedź zawiera poprawne dane pomiarowe.
        """
        if not isinstance(data, dict):
            return False
            
        measurement_keys = ['Lista danych pomiarowych', 'values', 'data', 'measurements', 'result']
        for key in measurement_keys:
            if key in data and isinstance(data[key], list) and len(data[key]) > 0:
                return True
        return False

    def _extract_measurements(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Wyodrębnia listę pomiarów z odpowiedzi API.
        """
        measurement_keys = ['Lista danych pomiarowych', 'values', 'data', 'measurements', 'result']
        for key in measurement_keys:
            if key in data and isinstance(data[key], list):
                return data[key]
        return []

    def _is_historical_data(self, measurements: List[Dict[str, Any]], start_date: str, end_date: str) -> bool:
        """
        Sprawdza czy dane mieszczą się w żądanym zakresie historycznym.
        """
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            historical_dates = 0
            for measurement in measurements[:10]:  # Check first 10 measurements
                if isinstance(measurement, dict):
                    date_str = measurement.get('Data') or measurement.get('date')
                else:
                    date_str = None

                if not date_str:
                    continue

                try:
                    for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']:
                        try:
                            measure_dt = datetime.strptime(date_str, fmt)
                            if start_dt <= measure_dt <= end_dt:
                                historical_dates += 1
                            break
                        except ValueError:
                            continue
                except Exception:
                    continue
            
            return historical_dates > 0  # Consider it historical if we found at least one date in range
            
        except ValueError:
            return False

    def get_air_quality_index(self, station_id: int) -> Optional[Dict[str, Any]]:
        """
        Pobiera indeks jakości powietrza dla danego ID stacji.
        """
        print(f"Fetching air quality index for station {station_id}...")
        return self._make_request(f"aqindex/getIndex/{station_id}")

    def get_processed_measurements(self, sensor_id: int, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """
        Pobiera i przetwarza dane pomiarowe dla danego ID czujnika.
        Returns processed measurements with datetime objects.
        """
        print(f"Fetching and processing measurements for sensor {sensor_id} from {start_date} to {end_date}...")
        raw_data = self.get_measurements_for_sensor(sensor_id, start_date, end_date)
        
        if not raw_data:
            return []
            
        return self.process_measurement_data(raw_data)

    def test_historical_data_access(self, sensor_id: int) -> Dict[str, Any]:
        """
        Testuje dostęp do danych historycznych dla różnych zakresów czasowych.
        """
        print("=" * 60)
        print("TESTING HISTORICAL DATA ACCESS")
        print("=" * 60)
        
        test_cases = [
            {"start": "2025-09-20", "end": "2025-09-24", "desc": "Ostatni tydzień"},
            {"start": "2025-09-01", "end": "2025-09-10", "desc": "Wcześniej w tym miesiącu"},
            {"start": "2024-01-01", "end": "2024-01-02", "desc": "Zeszły rok"},
        ]
        
        results = {}
        
        for test in test_cases:
            print(f"\n🔍 Testing: {test['desc']} ({test['start']} to {test['end']})")
            data = self.get_measurements_for_sensor(sensor_id, test['start'], test['end'])
            
            if data and self._has_valid_measurements(data):
                measurements = self._extract_measurements(data)
                if measurements:
                    dates = []
                    for item in measurements[:5]:  # Check first 5 measurements
                        if isinstance(item, dict) and 'Data' in item:
                            dates.append(item['Data'])
                    
                    if dates:
                        results[test['desc']] = {
                            'success': True,
                            'measurements_count': len(measurements),
                            'date_range': f"{min(dates)} to {max(dates)}",
                            'dates_sample': dates
                        }
                        print(f"✅ SUKCES: {len(measurements)} pomiarów, daty: {min(dates)} do {max(dates)}")
                    else:
                        results[test['desc']] = {'success': False, 'reason': 'Brak poprawnych dat'}
                        print("❌ BRAK: Nie znaleziono poprawnych dat w odpowiedzi")
                else:
                    results[test['desc']] = {'success': False, 'reason': 'Brak pomiarów'}
                    print("❌ BRAK: Nie wyodrębniono pomiarów")
            else:
                results[test['desc']] = {'success': False, 'reason': 'Brak danych z API'}
                print("❌ BRAK: Brak danych z API")
            
            # Rate limiting
            time.sleep(1)
        
        return results

    @staticmethod
    def process_measurement_data(raw_measurements_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Przetwarza surowe dane pomiarowe na gotowy format.
        Returns list of measurements with datetime objects.
        """
        if not isinstance(raw_measurements_data, dict):
            print("Error: Raw measurements data is not a dictionary")
            return []

        # GIOŚ API structure: data is under "Lista danych pomiarowych" with Polish keys
        measurements_list = []
        
        if 'Lista danych pomiarowych' in raw_measurements_data:
            measurements_list = raw_measurements_data['Lista danych pomiarowych']
        elif 'values' in raw_measurements_data:
            measurements_list = raw_measurements_data['values']
        elif 'data' in raw_measurements_data:
            measurements_list = raw_measurements_data['data']
        else:
            print("Error: No valid measurements data found in response")
            print(f"Available keys: {list(raw_measurements_data.keys())}")
            return []

        if not isinstance(measurements_list, list):
            print(f"Error: Measurements data is not a list, type: {type(measurements_list)}")
            return []

        processed_values = []
        for i, item in enumerate(measurements_list):
            if not isinstance(item, dict):
                continue
                
            try:
                # Extract date and value supporting both Polish and English keys
                date_str = (
                    item.get('Data')
                    or item.get('date')
                    or item.get('timestamp')
                    or item.get('TimeStamp')
                )
                value_raw = item.get('Wartość')
                if value_raw is None:
                    value_raw = item.get('value')
                
                # Debug first few items
                if i < 3:
                    print(f"Raw measurement item {i}: date='{date_str}', value='{value_raw}'")

                # Parse date
                parsed_date = None
                if date_str:
                    try:
                        # Try different date formats
                        for fmt in [
                            '%Y-%m-%d %H:%M:%S',
                            '%Y-%m-%dT%H:%M:%S',
                            '%Y-%m-%dT%H:%M:%S%z',
                            '%Y-%m-%d'
                        ]:
                            try:
                                parsed_date = datetime.strptime(str(date_str), fmt)
                                if parsed_date.tzinfo:
                                    parsed_date = parsed_date.replace(tzinfo=None)
                                break
                            except ValueError:
                                continue
                        if parsed_date is None:
                            print(f"Could not parse date: {date_str}")
                            continue
                    except (ValueError, TypeError) as e:
                        print(f"Date parsing error for '{date_str}': {e}")
                        continue
                
                # Parse value
                parsed_value = None
                if value_raw is not None:
                    try:
                        parsed_value = float(value_raw)
                    except (ValueError, TypeError) as e:
                        print(f"Value parsing error for '{value_raw}': {e}")
                        continue
                
                if parsed_date is not None and parsed_value is not None:
                    processed_values.append({
                        'date': parsed_date,  # This is a datetime object
                        'value': parsed_value
                    })
                else:
                    if i < 10:  # Limit debug output
                        print(f"Skipping invalid measurement: date='{date_str}', value='{value_raw}'")

            except Exception as e:
                print(f"Error processing measurement item {i}: {e}")
                continue

        print(f"Successfully processed {len(processed_values)} measurements")
        
        # Sort by date (newest first)
        processed_values.sort(key=lambda x: x['date'], reverse=True)
        print(f"Sorted {len(processed_values)} measurements by date")
        
        return processed_values
