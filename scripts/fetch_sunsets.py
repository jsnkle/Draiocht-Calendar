#!/usr/bin/env python3
"""Import USNO sunset tables for the Orlando reference calendars."""

import argparse
from datetime import date, datetime, timedelta, timezone
from html import unescape
import json
from pathlib import Path
import re
from urllib.parse import urlencode

from fetch_astronomy import YEARS, iso, read_source

ROOT = Path(__file__).resolve().parents[1]
LOCATION = {"name": "Orlando, Florida", "latitude": 28.54, "longitude": -81.38,
            "timezone": "America/New_York"}
STANDARD_TIME = timezone(timedelta(hours=-5))


def source_url(year):
    return "https://aa.usno.navy.mil/calculated/rstt/year?" + urlencode({
        "ID": "Draiocht", "year": year, "task": 0, "lat": LOCATION["latitude"],
        "lon": LOCATION["longitude"], "label": LOCATION["name"], "tz": 5, "tz_sign": -1,
    })


def parse_sunsets(body, year, source):
    match = re.search(r"<pre\b[^>]*>(.*?)</pre>", body, re.S | re.I)
    if not match:
        raise ValueError("Missing USNO annual table")
    table = unescape(re.sub(r"<[^>]*>", "", match[1]))
    if (f"Rise and Set for the Sun for {year}" not in table
            or not re.search(r"Zone:\s+5h West of Greenwich", table)
            or "Location: W081 23, N28 32" not in table):
        raise ValueError("Unexpected year, timezone, or location in Orlando sunset table")
    events = {}
    for line in table.splitlines():
        if not re.match(r"^\d{2}  ", line):
            continue
        day = int(line[:2])
        for month in range(1, 13):
            try:
                local_date = date(year, month, day)
            except ValueError:
                continue
            clock = line[9 + 11*(month-1):13 + 11*(month-1)]
            if not re.fullmatch(r"\d{4}", clock):
                raise ValueError(f"Missing sunset on {local_date}; no substitute day boundary is defined")
            if local_date in events:
                raise ValueError(f"Duplicate sunset on {local_date}")
            at = datetime(year, month, day, int(clock[:2]), int(clock[2:]), tzinfo=STANDARD_TIME)
            events[local_date] = {"utc": iso(at), "source": source}
    if len(events) != (date(year+1, 1, 1) - date(year, 1, 1)).days:
        raise ValueError(f"Incomplete sunset coverage for {year}")
    return [events[key] for key in sorted(events)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path)
    parser.add_argument("--retrieved-on", help="Original retrieval date, required with --cache-dir")
    args = parser.parse_args()
    if args.cache_dir and not args.retrieved_on:
        parser.error("--cache-dir requires --retrieved-on")
    retrieved = (datetime.strptime(args.retrieved_on, "%Y-%m-%d").date().isoformat()
                 if args.retrieved_on else datetime.now(timezone.utc).date().isoformat())
    data = {"retrieved_on": retrieved, "location": LOCATION,
            "definition": "Upper edge of the Sun at a level horizon, with standard refraction; USNO predicted sunset, to one minute.",
            "sources": [], "sunsets": []}
    for year in YEARS:
        url = source_url(year)
        body = read_source(url, f"sunsets-orlando-{year}.html", args.cache_dir).decode("utf-8")
        data["sunsets"].extend(parse_sunsets(body, year, url))
        data["sources"].append({"url": url, "publisher": "US Naval Observatory", "year": year,
                                "original_timezone": "Eastern Standard Time (UTC-05:00), all year"})
    destination = ROOT / "data/sunsets-orlando.json"
    destination.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print(f"Saved {len(data['sunsets'])} Orlando sunsets.")


if __name__ == "__main__":
    main()
