from datetime import timedelta
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_calendars as calendar
import fetch_astronomy as importer
import fetch_sunsets as sunset_importer


class CalendarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = calendar.load()
        cls.moons, cls.names = calendar.model(cls.data)
        cls.zone = ZoneInfo("America/New_York")
        cls.sunset_data = calendar.load_sunsets()
        cls.sunsets = [calendar.instant(e["utc"]) for e in cls.sunset_data["sunsets"]]

    def test_archive_is_byte_identical(self):
        manifest = json.loads((ROOT / "archive/manifest.json").read_text())
        self.assertEqual(len(manifest["files"]), 17)
        for record in manifest["files"]:
            body = (ROOT / "archive/2025-draft" / record["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(body).hexdigest(), record["sha256"], record["path"])

    def test_reference_solar_times_and_timezone_conversion(self):
        # Independent, manually checked NAOJ entries in Japanese standard time.
        expected = {
            (2026, 45): "2026-05-05T20:49:00+09:00",
            (2026, 90): "2026-06-21T17:25:00+09:00",
            (2026, 225): "2026-11-07T18:52:00+09:00",
            (2027, 0): "2027-03-21T05:25:00+09:00",
            (2028, 315): "2028-02-04T16:31:00+09:00",
            (2028, 0): "2028-03-20T11:17:00+09:00",
        }
        for key, value in expected.items():
            event = next(e for e in self.data["solar_markers"]
                         if (calendar.instant(e["utc"]).year, e["longitude"]) == key)
            self.assertEqual(calendar.instant(event["utc"]), calendar.instant(value))

    def test_reference_new_moon(self):
        # USNO March 2026: March 19, 01:23 UTC, the evening of March 18 in Orlando.
        at = calendar.instant("2026-03-19T01:23Z")
        self.assertIn(at, self.moons)
        self.assertEqual(calendar.stamp(at, self.zone), "2026-03-18 21:23 EDT")
        # USNO February/March 2028 bracket the closing Idir-Ré of 2027–2028.
        for value in ("2028-02-25T10:37Z", "2028-03-26T04:31Z"):
            self.assertIn(calendar.instant(value), self.moons)

    def test_year_changes_without_resetting_month_or_day(self):
        before = calendar.lookup(self.data, calendar.instant("2026-03-20T14:45:59Z"), self.zone)
        after = calendar.lookup(self.data, calendar.instant("2026-03-20T14:46Z"), self.zone)
        self.assertEqual((before["year"], after["year"]), ("2025–2026", "2026–2027"))
        self.assertEqual((before["month"], after["month"]), ("Idir-Ré", "Idir-Ré"))
        self.assertEqual((before["day"], after["day"]), (2, 2))
        self.assertEqual(before["threshold_section"], "before equinox")
        self.assertEqual(after["threshold_section"], "after equinox")

    def test_daytime_new_moon_is_day_one_from_previous_sunset(self):
        at = calendar.instant("2026-04-17T11:52Z")
        before = calendar.lookup(self.data, at - timedelta(seconds=1), self.zone)
        after = calendar.lookup(self.data, at, self.zone)
        self.assertEqual((before["month"], before["day"]), ("Éirí", 1))
        self.assertEqual((after["month"], after["day"]), ("Éirí", 1))
        self.assertEqual(before["year"], after["year"])
        self.assertEqual(calendar.instant(after["month_start_utc"]), calendar.instant("2026-04-16T23:52Z"))
        sunset = calendar.instant(after["month_start_utc"])
        ending = calendar.lookup(self.data, sunset-timedelta(seconds=1), self.zone)
        beginning = calendar.lookup(self.data, sunset, self.zone)
        self.assertEqual((ending["month"], beginning["month"], beginning["day"]), ("Idir-Ré", "Éirí", 1))

    def test_evening_new_moon_midnight_and_next_sunset(self):
        # March 18 sunset is 19:36 EDT; conjunction is later that evening at 21:23.
        sunset = calendar.instant("2026-03-18T23:36Z")
        before = calendar.lookup(self.data, sunset-timedelta(seconds=1), self.zone)
        self.assertEqual(before["month"], "Síneadh")
        for value in ("2026-03-18T23:36Z", "2026-03-19T01:22:59Z",
                      "2026-03-19T01:23Z", "2026-03-19T03:59:59Z", "2026-03-19T04:00Z",
                      "2026-03-19T23:35:59Z"):
            result = calendar.lookup(self.data, calendar.instant(value), self.zone)
            self.assertEqual((result["month"], result["day"]), ("Idir-Ré", 1))
        next_day = calendar.lookup(self.data, calendar.instant("2026-03-19T23:36Z"), self.zone)
        self.assertEqual((next_day["month"], next_day["day"]), ("Idir-Ré", 2))

    def test_conjunction_at_sunset_belongs_to_new_day(self):
        sunset = calendar.instant("2026-04-16T23:52Z")
        for seconds, expected_day in ((-1, 2), (0, 1), (1, 1)):
            data = json.loads(json.dumps(self.data))
            moon = next(e for e in data["new_moons"] if e["utc"].startswith("2026-04"))
            moon["utc"] = (sunset+timedelta(seconds=seconds)).isoformat()
            result = calendar.lookup(data, sunset, self.zone)
            self.assertEqual((result["month"], result["day"]), ("Éirí", expected_day))

    def test_equinox_before_conjunction_in_same_day_is_idir_re(self):
        data = json.loads(json.dumps(self.data))
        moon = next(e for e in data["new_moons"] if e["utc"].startswith("2026-03"))
        moon["utc"] = "2026-03-20T16:00Z"
        before = calendar.lookup(data, calendar.instant("2026-03-20T14:45:59Z"), self.zone)
        after = calendar.lookup(data, calendar.instant("2026-03-20T14:46Z"), self.zone)
        self.assertEqual((before["month"], after["month"], before["day"], after["day"]),
                         ("Idir-Ré", "Idir-Ré", 1, 1))
        self.assertEqual((before["year"], after["year"]), ("2025–2026", "2026–2027"))

    def test_display_timezone_does_not_relocate_observer(self):
        at = calendar.instant("2026-03-19T01:23Z")
        local = calendar.lookup(self.data, at, self.zone)
        other = calendar.lookup(self.data, at, ZoneInfo("Europe/Dublin"))
        for key in ("day", "month", "day_start_utc", "day_end_utc", "location"):
            self.assertEqual(local[key], other[key])
        self.assertNotEqual(local["day_start_local"], other["day_start_local"])

    def test_complete_days_and_local_month_coverage(self):
        moons, sunsets, starts, boundaries, names = calendar.daily_model(self.data, self.sunset_data)
        for index, moon in enumerate(moons):
            self.assertLessEqual(boundaries[index], moon)
            self.assertLess(moon, sunsets[starts[index]+1])
        for year in (2025, 2026, 2027):
            start, end = calendar.year_bounds(self.data, year)
            first, last = [calendar.month_index(boundaries, at) for at in (start, end)]
            portions = [min(end, boundaries[i+1])-max(start, boundaries[i]) for i in range(first, last+1)]
            self.assertEqual(sum(portions, timedelta()), end-start)
            for i in range(first, last+1):
                self.assertIn(starts[i+1]-starts[i], (29, 30))
            self.assertEqual((names[first], names[last]), ("Idir-Ré", "Idir-Ré"))

    def test_reference_sunset_import_and_missing_data_rejection(self):
        # Preserved USNO annual table; all input clock times are standard time.
        body = (ROOT / "tests/fixtures/sunsets-orlando-2026.html").read_text()
        events = sunset_importer.parse_sunsets(body, 2026, "test")
        self.assertEqual(len(events), 365)
        times = [calendar.instant(e["utc"]) for e in events]
        for value in ("2026-03-18T23:36Z", "2026-04-16T23:52Z", "2026-11-08T22:36Z"):
            self.assertIn(calendar.instant(value), times)
        self.assertEqual(calendar.stamp(times[76], self.zone), "2026-03-18 19:36 EDT")
        for invalid in (body.replace("5h West", "4h West"), body.replace("for 2026", "for 2027"),
                        body.replace("W081 23, N28 32", "W074 00, N40 43"),
                        body.replace("0718 1740", "0718     ", 1)):
            with self.assertRaises(ValueError):
                sunset_importer.parse_sunsets(invalid, 2026, "test")
        broken = json.loads(json.dumps(self.sunset_data))
        broken["sunsets"].pop(77)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sunsets.json"
            path.write_text(json.dumps(broken))
            with self.assertRaises(ValueError):
                calendar.load_sunsets(path)

    def test_daylight_saving_changes_do_not_change_lunar_duration(self):
        start = calendar.instant("2027-03-08T09:29Z")
        end = calendar.instant("2027-04-06T23:51Z")
        self.assertEqual(calendar.duration(end - start), "29d 14h 22m")
        self.assertTrue(calendar.stamp(start, self.zone).endswith("EST"))
        self.assertTrue(calendar.stamp(end, self.zone).endswith("EDT"))
        first = calendar.lookup(self.data, calendar.instant("2026-11-01T05:30Z"), self.zone)
        second = calendar.lookup(self.data, calendar.instant("2026-11-01T06:30Z"), self.zone)
        self.assertEqual(first["day"], second["day"])

    def test_year_coverage_and_distinct_month_counts(self):
        for year, cycles, whole in ((2025, 13, 12), (2026, 12, 11), (2027, 12, 11)):
            start, end = calendar.year_bounds(self.data, year)
            first, last = [calendar.month_index(self.moons, at) for at in (start, end)]
            self.assertEqual(last - first, cycles)
            self.assertEqual(sum(start <= self.moons[i] and self.moons[i+1] <= end
                                 for i in range(first, last+1)), whole)
            portions = [min(end, self.moons[i+1]) - max(start, self.moons[i]) for i in range(first, last+1)]
            self.assertEqual(sum(portions, timedelta()), end - start)
            self.assertGreater((end-start).total_seconds()/86400, 365)
            self.assertLess((end-start).total_seconds()/86400, 366)

    def test_black_moon_is_third_of_four_in_summer_2025(self):
        season_start = calendar.instant("2025-06-21T02:42Z")
        season_end = calendar.instant("2025-09-22T18:19Z")
        season = [moon for moon in self.moons if season_start <= moon < season_end]
        self.assertEqual([moon.strftime("%Y-%m-%d") for moon in season],
                         ["2025-06-25", "2025-07-24", "2025-08-23", "2025-09-21"])
        at = calendar.instant("2025-08-24T12:00Z")
        self.assertEqual(calendar.lookup(self.data, at, self.zone)["month"], "Ré Anann")
        self.assertEqual(self.moons[calendar.month_index(self.moons, at)], season[2])
        for year in (2026, 2027):
            start, end = calendar.year_bounds(self.data, year)
            self.assertNotIn("Ré Anann", [self.names[i] for i in range(len(self.moons)-1)
                                         if self.moons[i] < end and self.moons[i+1] > start])

    def test_revised_names_follow_the_solar_cycle(self):
        for year in (2025, 2026, 2027):
            start, end = calendar.year_bounds(self.data, year)
            first, last = [calendar.month_index(self.moons, at) for at in (start, end)]
            ordinary = [self.names[i] for i in range(first, last+1)
                        if self.names[i] != "Ré Anann"]
            self.assertEqual(ordinary, ["Idir-Ré", "Éirí", "Neartú", "Grian Thuaidh",
                                        "Iompú", "Giorrú", "Cothromú", "Ísliú", "Doimhniú",
                                        "Grian Theas", "Filleadh", "Síneadh", "Idir-Ré"])
            autumn = next(calendar.instant(e["utc"]) for e in self.data["solar_markers"]
                          if e["longitude"] == 180 and e["utc"].startswith(str(year)))
            self.assertEqual(calendar.lookup(self.data, autumn, self.zone)["month"], "Cothromú")

    def test_2027_year_boundaries_and_2028_lookup(self):
        start, end = calendar.year_bounds(self.data, 2027)
        self.assertEqual(start, calendar.instant("2027-03-20T20:25Z"))
        self.assertEqual(end, calendar.instant("2028-03-20T02:17Z"))
        self.assertEqual(calendar.duration(end-start), "365d 5h 52m")
        self.assertEqual(calendar.stamp(end, self.zone), "2028-03-19 22:17 EDT")
        imbolc = calendar.lookup(self.data, calendar.instant("2028-02-04T07:31Z"), self.zone)
        self.assertEqual((imbolc["year"], imbolc["month"]), ("2027–2028", "Síneadh"))
        last = calendar.lookup(self.data, end-timedelta(seconds=1), self.zone)
        self.assertEqual((last["year"], last["month"], last["threshold_section"]),
                         ("2027–2028", "Idir-Ré", "before equinox"))

    def test_black_moon_count_includes_opening_season_boundary(self):
        base = calendar.instant("2026-01-01T00:00Z")
        moons = [base + timedelta(days=29*i) for i in range(6)]
        # Four conjunctions when the season opens at the first one; three
        # when it opens a second later. The anchor-month spacing is unchanged.
        solar = [{"longitude": 0, "utc": base.isoformat()},
                 {"longitude": 90, "utc": (base + timedelta(days=90)).isoformat()}]
        names = calendar.assign_names(moons, solar)
        self.assertEqual(names[0], "Idir-Ré")
        self.assertEqual(names[2], "Ré Anann")
        self.assertEqual(names[3], "Grian Thuaidh")
        self.assertTrue(names[1].startswith("Lunation "))
        self.assertEqual(len(names), len(moons)-1)
        solar[0]["utc"] = (base + timedelta(seconds=1)).isoformat()
        names = calendar.assign_names(moons, solar)
        self.assertNotIn("Ré Anann", names.values())
        self.assertEqual((names[1], names[2]), ("Éirí", "Neartú"))

    def test_black_moon_count_excludes_closing_season_boundary(self):
        base = calendar.instant("2026-01-01T00:00Z")
        moons = [base + timedelta(days=29*i) for i in range(6)]
        # Synthetic span to isolate boundary ownership. Three conjunctions
        # are inside; a fourth exactly at the closing boundary is outside.
        solar = [{"longitude": 0, "utc": (base + timedelta(days=1)).isoformat()},
                 {"longitude": 90, "utc": moons[4].isoformat()}]
        names = calendar.assign_names(moons, solar)
        self.assertNotIn("Ré Anann", names.values())
        self.assertEqual(names[4], "Grian Thuaidh")
        self.assertTrue(all(names[i].startswith("Lunation ") for i in (1, 2, 3)))
        self.assertEqual(len(names), len(moons)-1)
        solar[1]["utc"] = (moons[4] + timedelta(seconds=1)).isoformat()
        names = calendar.assign_names(moons, solar)
        self.assertEqual((names[1], names[2], names[3]), ("Éirí", "Neartú", "Ré Anann"))

    def test_simultaneous_equinox_and_new_moon_belong_to_new_interval(self):
        data = json.loads(json.dumps(self.data))
        event = next(e for e in data["solar_markers"] if e["longitude"] == 0 and e["utc"].startswith("2026"))
        event["utc"] = "2026-03-19T01:23Z"
        result = calendar.lookup(data, calendar.instant(event["utc"]), self.zone)
        self.assertEqual((result["year"], result["month"], result["day"], result["threshold_section"]),
                         ("2026–2027", "Idir-Ré", 1, "after equinox"))

    def test_unusual_naming_arrangement_keeps_months(self):
        moons = [calendar.instant("2026-01-01T00:00Z") + timedelta(days=29*i) for i in range(8)]
        # Deliberately synthetic coverage, testing the fallback rather than astronomy.
        solar = [{"longitude": 0, "utc": "2026-01-02T00:00Z"},
                 {"longitude": 90, "utc": "2026-03-01T00:00Z"}]
        names = calendar.assign_names(moons, solar)
        self.assertEqual(names[0], "Idir-Ré")
        self.assertEqual(names[2], "Grian Thuaidh")
        self.assertTrue(names[1].startswith("Lunation "))
        self.assertEqual(len(names), len(moons)-1)

    def test_invalid_and_unsupported_dates_fail(self):
        with self.assertRaises(ValueError):
            calendar.instant("2026-03-20T10:46")
        for value in ("2025-01-01T00:00Z", "2028-03-20T02:17Z"):
            with self.assertRaises(ValueError):
                calendar.lookup(self.data, calendar.instant(value), self.zone)

    def test_incomplete_solar_source_is_rejected(self):
        with self.assertRaises(ValueError):
            importer.parse_solar("<html>Unavailable</html>", 2026, "test")

    def test_long_range_solar_source(self):
        body = (ROOT / "tests/fixtures/solar-2028.html").read_text()
        events = importer.parse_solar(body, 2028, "test")
        self.assertEqual(len(events), 8)
        self.assertEqual(next(e["utc"] for e in events if e["longitude"] == 315),
                         "2028-02-04T07:31Z")
        self.assertEqual(next(e["utc"] for e in events if e["longitude"] == 0),
                         "2028-03-20T02:17Z")
        # A default-year response or altered time zone must not silently import.
        with self.assertRaises(ValueError):
            importer.parse_solar(body, 2027, "test")
        with self.assertRaises(ValueError):
            importer.parse_solar(body.replace("LST:UT+9", "LST:UT+8"), 2028, "test")
        with self.assertRaises(ValueError):
            importer.parse_solar(body.replace("315&deg;", "300&deg;"), 2028, "test")

    def test_checked_in_calendars_are_reproducible(self):
        for year in (2025, 2026, 2027):
            self.assertEqual((ROOT / f"calendars/{year}-{year+1}.md").read_text(),
                             calendar.render_year(self.data, year, self.zone))


if __name__ == "__main__":
    unittest.main()
