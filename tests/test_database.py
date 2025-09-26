import os
import tempfile
import unittest
from datetime import datetime, timedelta

from air_quality.database import AirQualityDatabase


class AirQualityDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        db_path = os.path.join(self.tmpdir.name, "test.db")
        self.db = AirQualityDatabase(db_path)

    def tearDown(self):
        self.db.close()
        self.tmpdir.cleanup()

    def test_save_and_query_measurements(self):
        base_time = datetime(2023, 5, 1, 12, 0, 0)
        measurements = [
            {"date": base_time - timedelta(hours=i), "value": 10 + i}
            for i in range(3)
        ]

        inserted = self.db.save_measurements(sensor_id=42, measurements=measurements, station_id=1, param_code="PM10")
        self.assertEqual(inserted, 3)

        all_rows = self.db.get_measurements(42)
        self.assertEqual(len(all_rows), 3)
        self.assertEqual(all_rows[0]["sensor_id"], 42)

        filtered = self.db.get_measurements(42, start_date=base_time - timedelta(hours=1), end_date=base_time)
        self.assertEqual(len(filtered), 2)


if __name__ == "__main__":
    unittest.main()
