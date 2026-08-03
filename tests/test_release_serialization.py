from __future__ import annotations

import unittest
from datetime import date, datetime, timezone

from apps.api.app.release_routes import _json


class ExportSerializationTests(unittest.TestCase):
    def test_postgres_date_and_datetime_values_are_iso_serialized(self):
        self.assertEqual(_json(date(2026, 7, 30)), "2026-07-30")
        self.assertEqual(
            _json(datetime(2026, 7, 30, 8, 9, tzinfo=timezone.utc)),
            "2026-07-30T08:09:00+00:00",
        )


if __name__ == "__main__":
    unittest.main()
