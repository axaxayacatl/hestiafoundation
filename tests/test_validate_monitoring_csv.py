
import tempfile
import unittest
from pathlib import Path

from tools.validate_monitoring_csv import validate_csv


class ValidateCsvTests(unittest.TestCase):
    def check_csv(self, content: str) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "monitoring.csv"
            path.write_text(content, encoding="utf-8")
            return validate_csv(path)

    def test_valid_record(self):
        errors = self.check_csv(
            "timestamp,sensor_id,location,temperature_c,humidity_pct\n"
            "2026-10-19T12:00:00Z,IN-1,north_wall,22.5,50\n"
        )
        self.assertEqual(errors, [])

    def test_missing_required_column(self):
        errors = self.check_csv(
            "timestamp,sensor_id\n"
            "2026-10-19T12:00:00Z,IN-1\n"
        )
        self.assertTrue(
            any("Missing required columns" in e for e in errors),
            errors,
        )

    def test_invalid_timestamp(self):
        errors = self.check_csv(
            "timestamp,sensor_id,location\n"
            "not-a-date,IN-1,north_wall\n"
        )
        self.assertTrue(
            any("invalid ISO 8601 timestamp" in e for e in errors),
            errors,
        )

    def test_invalid_numeric_measurement(self):
        errors = self.check_csv(
            "timestamp,sensor_id,location,temperature_c\n"
            "2026-10-19T12:00:00Z,IN-1,north_wall,hot\n"
        )
        self.assertTrue(
            any("finite number" in e for e in errors),
            errors,
        )


if __name__ == "__main__":
    unittest.main()
