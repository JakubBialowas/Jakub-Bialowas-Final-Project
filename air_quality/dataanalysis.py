"""
Data analysis module for air quality measurements.
Provides statistical analysis and trend detection.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import statistics
from scipy import stats
import sqlite3


class AirQualityAnalyzer:
    """Analyzer for air quality measurement data."""
    
    @staticmethod
    def analyze_measurements(measurements: List[Dict]) -> Dict[str, Any]:
        """
        Perform comprehensive statistical analysis on measurement data.
        
        Args:
            measurements: List of measurement dictionaries with 'value' and 'date' keys
            
        Returns:
            Dictionary with analysis results including statistics and trend information
        """
        # Filter out None values and invalid measurements
        valid_measurements = [m for m in measurements if m.get('value') is not None and isinstance(m.get('value'), (int, float))]
        values = [m['value'] for m in valid_measurements]
        dates = [m['date'] for m in valid_measurements]
        
        if not values:
            return {
                "min_value": None,
                "max_value": None,
                "avg_value": None,
                "median_value": None,
                "std_dev": None,
                "min_date": None,
                "max_date": None,
                "trend": None,
                "trend_direction": "brak danych",
                "trend_strength": None,
                "count": 0,
                "data_range": None
            }
        
        # Basic statistics
        min_value = min(values)
        max_value = max(values)
        avg_value = statistics.mean(values)
        median_value = statistics.median(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0
        data_range = max_value - min_value
        
        # Find dates for min and max values
        min_index = values.index(min_value)
        max_index = values.index(max_value)
        min_date = dates[min_index]
        max_date = dates[max_index]
        
        # Calculate trend and its statistical significance
        trend, trend_strength = AirQualityAnalyzer._calculate_trend_with_significance(dates, values)
        
        # Determine trend direction
        if trend > 0.1:
            trend_direction = "wzrostowa"
        elif trend < -0.1:
            trend_direction = "spadkowa"
        else:
            trend_direction = "stabilna"
        
        return {
            "min_value": min_value,
            "max_value": max_value,
            "avg_value": avg_value,
            "median_value": median_value,
            "std_dev": std_dev,
            "min_date": min_date,
            "max_date": max_date,
            "trend": trend,
            "trend_direction": trend_direction,
            "trend_strength": trend_strength,
            "count": len(values),
            "data_range": data_range
        }
    
    @staticmethod
    def _calculate_trend_with_significance(dates: List[str], values: List[float]) -> Tuple[float, str]:
        """
        Calculate the trend of measurements using linear regression with significance test.
        
        Args:
            dates: List of date strings
            values: List of measurement values
            
        Returns:
            Tuple of (slope, strength) where strength is 'strong', 'moderate', 'weak', or 'insignificant'
        """
        if len(values) < 3:  # Need at least 3 points for meaningful trend analysis
            return 0.0, "niewystarczające dane"
        
        try:
            if isinstance(dates[0], datetime):
            # Mamy już datetime → wystarczy timestamp
                timestamps = [d.timestamp() for d in dates]
            else:
            # Próba parsowania stringów ISO
                timestamps = [datetime.fromisoformat(date.replace('Z', '+00:00')).timestamp() for date in dates]
        except (ValueError, TypeError, AttributeError):
            try:
                # Fallback dla formatu 'YYYY-MM-DD HH:MM:SS'
                timestamps = [datetime.strptime(str(date).split('.')[0], '%Y-%m-%d %H:%M:%S').timestamp() for date in dates]
            except Exception:
                # Ostateczny fallback – indeksy
                timestamps = list(range(len(dates)))

        
        # Calculate linear regression
        x = np.array(timestamps)
        y = np.array(values)
        
        # Normalize x to avoid large numbers and improve numerical stability
        x_normalized = (x - x.min()) / (x.max() - x.min()) if x.max() > x.min() else x
        
        # Calculate slope and intercept
        slope, intercept, r_value, p_value, std_err = stats.linregress(x_normalized, y)
        
        # Determine trend strength based on p-value and r-value
        if p_value < 0.01 and abs(r_value) > 0.7:
            strength = "silny"
        elif p_value < 0.05 and abs(r_value) > 0.5:
            strength = "umiarkowany"
        elif p_value < 0.1 and abs(r_value) > 0.3:
            strength = "słaby"
        else:
            strength = "nieistotny statystycznie"
        
        return slope, strength
    
    @staticmethod
    def get_air_quality_index_level(index_data: Dict) -> Optional[str]:
        """
        Extract air quality index level from index data.
        
        Args:
            index_data: Air quality index data dictionary
            
        Returns:
            Index level name or None if not available
        """
        if not index_data:
            return None
            
        # Check multiple possible locations for index level data
        st_index_level = index_data.get('stIndexLevel')
        if st_index_level and isinstance(st_index_level, dict):
            return st_index_level.get('indexLevelName')
        
        # Check for other possible key locations
        for key in index_data:
            if 'index' in key.lower() and isinstance(index_data[key], dict):
                level_name = index_data[key].get('indexLevelName')
                if level_name:
                    return level_name
        
        return None
    
    @staticmethod
    def calculate_statistics_from_db(conn: sqlite3.Connection, sensor_id: int, 
                                   start_date: Optional[str] = None, 
                                   end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate comprehensive statistics for measurement data of a given sensor.
        
        Args:
            conn: Active SQLite database connection
            sensor_id: Sensor ID for which to calculate statistics
            start_date: Optional start date for filtering (YYYY-MM-DD format)
            end_date: Optional end date for filtering (YYYY-MM-DD format)
            
        Returns:
            Dictionary containing comprehensive statistics
        """
        try:
            cursor = conn.cursor()
            
            # Build query with optional date filtering
            query = '''
                SELECT value, date
                FROM measurements
                WHERE sensorId = ? AND value IS NOT NULL
            '''
            params = [sensor_id]
            
            if start_date:
                query += ' AND date >= ?'
                params.append(start_date)
            if end_date:
                query += ' AND date <= ?'
                params.append(end_date)
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            if not results:
                return {"count": 0, "message": "Brak danych dla podanych parametrów"}
            
            values = [row[0] for row in results]
            timestamps = [row[1] for row in results]
            
            # Calculate comprehensive statistics
            min_value = min(values)
            max_value = max(values)
            avg_value = statistics.mean(values)
            median_value = statistics.median(values)
            std_dev = statistics.stdev(values) if len(values) > 1 else 0
            
            # Find timestamps for min and max values
            min_index = values.index(min_value)
            max_index = values.index(max_value)
            min_timestamp = timestamps[min_index]
            max_timestamp = timestamps[max_index]
            
            # Calculate trend
            trend, trend_strength = AirQualityAnalyzer._calculate_trend_with_significance(timestamps, values)
            
            return {
                'min': min_value,
                'max': max_value,
                'avg': round(avg_value, 2),
                'median': median_value,
                'std_dev': round(std_dev, 2),
                'min_timestamp': min_timestamp,
                'max_timestamp': max_timestamp,
                'trend': round(trend, 4),
                'trend_strength': trend_strength,
                'count': len(values),
                'data_range': max_value - min_value
            }
            
        except Exception as e:
            print(f"Błąd podczas obliczania statystyk z bazy danych: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def detect_anomalies(measurements: List[Dict], threshold: float = 2.0) -> List[Dict]:
        """
        Detect anomalous measurements using Z-score method.
        
        Args:
            measurements: List of measurement dictionaries
            threshold: Z-score threshold for anomaly detection (default: 2.0)
            
        Returns:
            List of anomalous measurements with their Z-scores
        """
        valid_measurements = [m for m in measurements if m.get('value') is not None]
        values = [m['value'] for m in valid_measurements]
        
        if len(values) < 3:
            return []
        
        mean = statistics.mean(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0
        
        if std_dev == 0:
            return []
        
        anomalies = []
        for i, measurement in enumerate(valid_measurements):
            z_score = abs((measurement['value'] - mean) / std_dev)
            if z_score > threshold:
                anomaly = measurement.copy()
                anomaly['z_score'] = z_score
                anomalies.append(anomaly)
        
        return anomalies
    
    @staticmethod
    def calculate_hourly_averages(measurements: List[Dict]) -> Dict[int, float]:
        """
        Calculate average values for each hour of the day.
        
        Args:
            measurements: List of measurement dictionaries with timestamps
            
        Returns:
            Dictionary mapping hour (0-23) to average value
        """
        hourly_values = {hour: [] for hour in range(24)}
        
        for measurement in measurements:
            if measurement.get('value') is not None and measurement.get('date'):
                try:
                    dt = datetime.fromisoformat(measurement['date'].replace('Z', '+00:00'))
                    hour = dt.hour
                    hourly_values[hour].append(measurement['value'])
                except (ValueError, TypeError):
                    continue
        
        hourly_averages = {}
        for hour, values in hourly_values.items():
            if values:
                hourly_averages[hour] = statistics.mean(values)
        
        return hourly_averages
