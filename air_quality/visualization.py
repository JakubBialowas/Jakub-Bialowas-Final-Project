import matplotlib.pyplot as plt
from datetime import datetime
import sqlite3
from typing import Optional

class DataVisualizer:
    def plot_data(conn: sqlite3.Connection, sensor_id: int, sensor_name: str = "Unknown"):
        """
        Tworzy i wyświetla wykres danych pomiarowych dla wybranego sensora.

        Args:
            conn: Połączenie z bazą danych SQLite.
            sensor_id (int): ID sensora, dla którego mają zostać wyświetlone dane.
            sensor_name (str): Nazwa sensora do wyświetlenia w tytule wykresu.
        """
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT date, value FROM measurements
                WHERE sensorId = ?
                ORDER BY date
            ''', (sensor_id,))
            data = cursor.fetchall()

            if not data:
                print("Brak danych do wyświetlenia.")
                return

            dates_str, values = zip(*data)
            
            # Konwersja dat z formatu string na obiekty datetime
            dates_dt = []
            for d in dates_str:
                try:
                    # Sprawdzamy różne formaty dat
                    dates_dt.append(datetime.strptime(d, '%Y-%m-%d %H:%M:%S'))
                except ValueError:
                    print(f"Błąd formatu daty dla: {d}. Używam surowego stringa.")
                    dates_dt.append(d)

            plt.figure(figsize=(10, 5))
            plt.plot(dates_dt, values, marker='o', linestyle='-', color='b')
            plt.xticks(rotation=45, ha='right')
            plt.title(f"Pomiary czujnika {sensor_name}", fontsize=16)
            plt.xlabel("Data", fontsize=12)
            plt.ylabel("Wartość", fontsize=12)
            plt.grid(True, which='both', linestyle='--', linewidth=0.5)
            plt.tight_layout()
            plt.show()

        except sqlite3.Error as e:
            print(f"Błąd bazy danych podczas pobierania danych do wykresu: {e}")
        except Exception as e:
            print(f"Wystąpił nieoczekiwany błąd: {e}")

    if __name__ == "__main__":
        # Ten blok testowy symuluje połączenie z bazą danych i dane.
        # Upewnij się, że masz testową bazę danych `test_data.db` z danymi.
        test_db_path = "data/test_data.db"
        conn = None
        try:
            conn = sqlite3.connect(test_db_path)
            print("Pomyślnie połączono z bazą danych.")
            
            # Przykładowe dane
            sample_data = [
                {'date': '2025-09-13 10:00:00', 'value': 25.5},
                {'date': '2025-09-13 11:00:00', 'value': 26.1},
                {'date': '2025-09-13 12:00:00', 'value': 24.8},
                {'date': '2025-09-13 13:00:00', 'value': 27.2}
            ]
            
            # Zapisujemy przykładowe dane do testu
            cursor = conn.cursor()
            cursor.execute("DELETE FROM measurements WHERE sensorId = 123")
            for data_point in sample_data:
                cursor.execute("INSERT INTO measurements (sensorId, date, value) VALUES (?, ?, ?)", 
                            (123, data_point['date'], data_point['value']))
            conn.commit()

            # Wyświetlamy wykres
            plot_data(conn, 123, "PM10")

        except sqlite3.Error as e:
            print(f"Błąd bazy danych podczas testowania modułu: {e}")
        finally:
            if conn:
                conn.close()