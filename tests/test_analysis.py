import unittest
from datetime import datetime

try:
    from air_quality.dataanalysis import AirQualityAnalyzer
    ANALYZER_AVAILABLE = True
    ANALYZER_IMPORT_ERROR = None
except Exception as exc:  # pragma: no cover - executed only when dependencies missing
    ANALYZER_AVAILABLE = False
    ANALYZER_IMPORT_ERROR = exc


@unittest.skipUnless(ANALYZER_AVAILABLE, f"AirQualityAnalyzer unavailable: {ANALYZER_IMPORT_ERROR}")
class AirQualityAnalyzerTests(unittest.TestCase):
    def test_analyze_measurements_basic_stats(self):
        sample = [
            {"date": datetime(2025, 1, 1, 10), "value": 10.0},
            {"date": datetime(2025, 1, 1, 11), "value": 20.0},
            {"date": datetime(2025, 1, 1, 12), "value": 30.0},
        ]

        result = AirQualityAnalyzer.analyze_measurements(sample)

        self.assertEqual(result["min_value"], 10.0)
        self.assertEqual(result["max_value"], 30.0)
        self.assertEqual(result["avg_value"], 20.0)
        self.assertEqual(result["count"], 3)
        self.assertIn(result["trend_direction"], {"wzrostowa", "stabilna"})


if __name__ == "__main__":
    unittest.main()
