# Astronomical data and regeneration

`astronomy.json` contains 49 new-moon times, 198 primary lunar phases (including those new moons), and 32 seasonal markers for Gregorian years 2025–2028. Every event retains its source URL. The data support the three complete solar-year calendars beginning at the vernal equinoxes of 2025, 2026, and 2027, with the lunar months crossing their boundaries. Seasonal names refer to the Northern Hemisphere.

`sunsets-orlando.json` contains 1,461 daily sunsets for the same years at the Orlando reference point, 28.54° N, 81.38° W. Each dated month begins at the sunset opening the day that contains its new moon. Daily numbering counts sunsets from that boundary.

## Sources and precision

- **New moons:** [US Naval Observatory API](https://aa.usno.navy.mil/data/api), from its annual primary-phase tables. The source times are UTC.
- **Solar markers:** National Astronomical Observatory of Japan, annual tables for [2025](https://eco.mtk.nao.ac.jp/koyomi/yoko/2025/rekiyou252.html.en), [2026](https://eco.mtk.nao.ac.jp/koyomi/yoko/2026/rekiyou262.html.en), and [2027](https://eco.mtk.nao.ac.jp/koyomi/yoko/2027/rekiyou272.html.en), plus its [long-range calculator for 2028](https://eco.mtk.nao.ac.jp/cgi-bin/koyomi/cande/phenomena_sy_en.cgi?year=2028&lst=9&phenom=50&cal=0&jg=1&dtm=0&dt=0&body=0&body=1&coord=1&figure=0). The source times are Japan Central Standard Time, UTC+09:00.
- **Sunsets:** [USNO annual rise/set tables](https://aa.usno.navy.mil/data/RS_OneYear), requested for Orlando in fixed Eastern Standard Time, UTC−05:00, throughout each source year. The importer converts these to UTC; the display applies daylight-saving time through America/New_York. Source URLs retain the requested coordinates and timezone.

The 2028 annual solar table was not yet available when these data were retrieved. Its long-range counterpart uses NAOJ's predicted ΔT setting, reported as 69 seconds for this calculation. The 2028 vernal equinox agrees with the [USNO season table](https://aa.usno.navy.mil/api/seasons?year=2028) at 02:17 UTC on March 20, which is 22:17 EDT on March 19 in Orlando. Future publications may revise predictions.

The importer converts events to UTC. The generator compares and subtracts UTC instants, then converts them to America/New_York for display, including daylight-saving transitions. Independent published tables can differ by a minute; the solar tables consistently use NAOJ. For example, NAOJ lists the June 2026 solstice one minute later than USNO.

Times are published to a minute. Rounded entries do not provide second-level precision, and near-coincident events require a higher-precision source. The original CSV and hand-written pattern analyses are not calculation inputs.

USNO sunset means the Sun's upper edge reaching a level horizon, with average atmospheric refraction. It precedes the end of twilight. Weather, terrain, and elevation affect observed sunset, so the table is a reference prediction. [USNO definitions](https://aa.usno.navy.mil/faq/RST_defs).

## Rebuild and verify

Python 3.9 or later and an available IANA time-zone database are required. No third-party Python packages are used.

From the repository root:

```sh
python3 scripts/build_calendars.py
python3 scripts/build_calendars.py --check
python3 -m unittest discover -s tests -v
```

Generation works offline from the committed data. To refresh the public source tables, with network access:

```sh
python3 scripts/fetch_astronomy.py
python3 scripts/fetch_sunsets.py
python3 scripts/build_calendars.py
```

The astronomical importer selects all eight angular markers and each new moon; it does not approximate them from average month lengths or fit an orbital model. The sunset importer requires a complete annual table for Orlando. The generator places day 1 at the sunset on or before conjunction, then assigns the quarter-point names to the dated months containing those events. It counts the exact new-moon instants within each astronomical season to identify its third new moon as a Black Moon when there are four, assigning Ré Anann to the month whose day 1 contains it. Season and day boundaries include their beginning and exclude their end.

The importers intentionally cover 2025–2028. Extending the range requires additional bounding astronomical events and sunsets, with a review of names where the usual arrangement fails.

## Look up a date

```sh
python3 scripts/build_calendars.py --at 2026-09-19T12:00:00-04:00
python3 scripts/build_calendars.py --at 2026-09-19T16:00:00Z --timezone Europe/Dublin
```

Supply an instant with an explicit offset. The result includes the solar year, month, day number, the day's opening and closing sunsets, the month's sunset boundaries, and its new-moon instant. It implements the [sunset-to-sunset rule](../docs/calendar-rules.md#daily-dates) for **Orlando**. The second example displays the same Orlando day boundaries on a Dublin clock; it does not relocate the observer.

For another location, supply `--sunsets path/to/local-sunsets.json` using the same structure as `sunsets-orlando.json`: location name, latitude, longitude, IANA timezone, and consecutive sunset events with explicit UTC timestamps and source URLs. The current generator requires sunset coverage bracketing every new moon in `astronomy.json`. A timezone alone cannot supply local sunsets. Incomplete coverage and unsupported dates fail; no substitute boundary is invented for days without sunset.
