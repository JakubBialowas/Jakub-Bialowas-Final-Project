"""SQLite persistence helpers for the air quality application."""

import sqlite3
import os
from datetime import datetime
from typing import Iterable, List, Optional, Dict, Any, Tuple

class AirQualityDatabase:
    def __init__(self, db_path="data/air_quality.db"):
        self.db_path = db_path
        
        try:
            # Create the data directory if it doesn't exist
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            self.conn = sqlite3.connect(db_path)
            self.conn.row_factory = sqlite3.Row
            self.create_tables()
            print(f"Database created successfully at: {db_path}")
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
            self.conn = None
        except Exception as e:
            print(f"Unexpected error creating database: {e}")
            self.conn = None

    def create_tables(self):
        if not self.conn:
            return
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stations (
                id INTEGER PRIMARY KEY,
                stationName TEXT,
                city TEXT,
                addressStreet TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sensorId INTEGER NOT NULL,
                date TEXT NOT NULL,
                value REAL,
                stationId INTEGER,
                paramCode TEXT,
                source TEXT,
                createdAt TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE UNIQUE INDEX IF NOT EXISTS idx_measurements_sensor_date
            ON measurements(sensorId, date)
        ''')
        self._ensure_columns(cursor)
        self.conn.commit()

    def _ensure_columns(self, cursor: sqlite3.Cursor) -> None:
        """Add optional columns if the database was created with an older schema."""

        cursor.execute("PRAGMA table_info(measurements)")
        existing_columns = {row[1] for row in cursor.fetchall()}

        migrations = {
            'stationId': "ALTER TABLE measurements ADD COLUMN stationId INTEGER",
            'paramCode': "ALTER TABLE measurements ADD COLUMN paramCode TEXT",
            'source': "ALTER TABLE measurements ADD COLUMN source TEXT",
            'createdAt': "ALTER TABLE measurements ADD COLUMN createdAt TEXT DEFAULT CURRENT_TIMESTAMP"
        }

        for column, statement in migrations.items():
            if column not in existing_columns:
                cursor.execute(statement)

    def save_measurements(
        self,
        sensor_id: int,
        measurements: Iterable[Dict[str, Any]],
        *,
        station_id: Optional[int] = None,
        param_code: Optional[str] = None,
        source: str = "api"
    ) -> int:
        """Persist measurements in the database and return number of inserted rows."""

        if not self.conn:
            return 0

        to_insert: List[Tuple[Any, ...]] = []
        for item in measurements:
            if not isinstance(item, dict):
                continue

            timestamp = item.get('date') or item.get('timestamp')
            value = item.get('value')

            if timestamp is None:
                continue

            if isinstance(timestamp, datetime):
                timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
            else:
                timestamp_str = str(timestamp)

            value_clean = None
            if value is not None:
                try:
                    value_clean = float(value)
                except (TypeError, ValueError):
                    continue

            to_insert.append((
                sensor_id,
                timestamp_str,
                value_clean,
                station_id,
                param_code,
                source
            ))

        if not to_insert:
            return 0

        cursor = self.conn.cursor()
        before = self.conn.total_changes
        cursor.executemany(
            '''
            INSERT OR IGNORE INTO measurements
            (sensorId, date, value, stationId, paramCode, source)
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            to_insert
        )
        self.conn.commit()
        return self.conn.total_changes - before

    def get_measurements(
        self,
        sensor_id: int,
        *,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Fetch measurements for a sensor constrained by optional date range."""

        if not self.conn:
            return []

        query = [
            "SELECT sensorId, date, value, stationId, paramCode FROM measurements WHERE sensorId = ?"
        ]
        params: List[Any] = [sensor_id]

        if start_date is not None:
            query.append("AND date >= ?")
            params.append(start_date.strftime('%Y-%m-%d %H:%M:%S'))
        if end_date is not None:
            query.append("AND date <= ?")
            params.append(end_date.strftime('%Y-%m-%d %H:%M:%S'))

        query.append("ORDER BY date DESC")

        cursor = self.conn.cursor()
        cursor.execute(" ".join(query), params)
        rows = cursor.fetchall()

        results: List[Dict[str, Any]] = []
        for row in rows:
            row_dict = dict(row)
            try:
                date_value = datetime.strptime(row_dict['date'], '%Y-%m-%d %H:%M:%S')
            except (ValueError, TypeError):
                try:
                    date_value = datetime.fromisoformat(row_dict['date'])
                except Exception:
                    date_value = None

            results.append({
                'sensor_id': row_dict.get('sensorId'),
                'date': date_value,
                'raw_date': row_dict.get('date'),
                'value': row_dict.get('value'),
                'station_id': row_dict.get('stationId'),
                'param_code': row_dict.get('paramCode')
            })

        return results

    def get_available_date_range(self, sensor_id: int) -> Optional[Tuple[str, str]]:
        """Return (min_date, max_date) for stored measurements of a sensor."""

        if not self.conn:
            return None

        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT MIN(date) AS min_date, MAX(date) AS max_date FROM measurements WHERE sensorId = ?",
            (sensor_id,)
        )
        row = cursor.fetchone()
        if not row or not row[0] or not row[1]:
            return None
        return row[0], row[1]

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
