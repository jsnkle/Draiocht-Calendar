#!/usr/bin/env python3
"""Import published observatory event times; no astronomical model is fitted here."""

import argparse
from datetime import datetime, timezone
from html import unescape
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
YEARS = (2025, 2026, 2027, 2028)
MARKERS = {
    0: "Vernal equinox", 45: "Beltane", 90: "Summer solstice",
    135: "Lughnasadh", 180: "Autumnal equinox", 225: "Samhain",
    270: "Winter solstice", 315: "Imbolc",
}


def iso(dt):
    return dt.astimezone(timezone.utc).isoformat(timespec="minutes").replace("+00:00", "Z")


def parse_solar(body, year, source):
    events = []
    for row in re.findall(r"<tr\b[^>]*>(.*?)</tr>", body, flags=re.S | re.I):
        cells = [unescape(re.sub(r"<[^>]*>", "", cell)).strip()
                 for cell in re.findall(r"<td\b[^>]*>(.*?)</td>", row, flags=re.S | re.I)]
        if len(cells) == 4 and cells[1].endswith("°"):
            longitude = int(cells[1][:-1])
            if longitude not in MARKERS or cells[0] == "Doyou":
                continue
            date_text = re.sub(r"(?<=\d)(st|nd|rd|th)\b", "", cells[2])
            day = datetime.strptime(f"{year} {date_text}", "%Y %B %d")
            match = re.fullmatch(r"(\d+)h(\d+)m", cells[3])
            if not match:
                raise ValueError(f"Unrecognized solar time: {cells}")
            day = day.replace(hour=int(match[1]), minute=int(match[2]))
        elif len(cells) == 6 and cells[2:4] == ["Sun", "24 Solar Terms"]:
            # NAOJ's long-range calculator supplies years not yet in its almanac.
            match = re.search(r"λ\s*=\s*(\d+)°", cells[5])
            if not match:
                raise ValueError(f"Unrecognized solar longitude: {cells}")
            longitude = int(match[1])
            if longitude not in MARKERS:
                continue
            day = datetime.strptime(f"{cells[0]} {cells[1]}", "%Y-%m-%d %H:%M")
            if day.year != year:
                raise ValueError(f"Expected solar events for {year}, received {day.year}")
            if not re.search(r"LST:UT\+9<sup>h</sup>", body):
                raise ValueError("Expected Japan Central Standard Time in long-range solar data")
        else:
            continue
        instant = day.replace(tzinfo=ZoneInfo("Asia/Tokyo"))
        events.append({"utc": iso(instant), "longitude": longitude,
                       "name": MARKERS[longitude], "source": source})
    if len(events) != 8 or {e["longitude"] for e in events} != set(MARKERS):
        raise ValueError(f"Expected eight distinct solar markers for {year}")
    return events


def read_source(url, filename, cache):
    if cache:
        return (cache / filename).read_bytes()
    with urlopen(Request(url, headers={"User-Agent": "DraiochtCalendar/0.1"}), timeout=30) as response:
        return response.read()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, help="Use previously downloaded source files")
    parser.add_argument("--retrieved-on", help="Original retrieval date (YYYY-MM-DD), required with --cache-dir")
    args = parser.parse_args()
    if args.cache_dir and not args.retrieved_on:
        parser.error("--cache-dir requires --retrieved-on to preserve source provenance")
    retrieved = datetime.strptime(args.retrieved_on, "%Y-%m-%d").date().isoformat() if args.retrieved_on else datetime.now(timezone.utc).date().isoformat()
    data = {"retrieved_on": retrieved,
            "precision": "Published times rounded to one minute; not second-accurate observations.",
            "sources": [], "new_moons": [], "solar_markers": []}
    for year in YEARS:
        moon_url = f"https://aa.usno.navy.mil/api/moon/phases/year?year={year}"
        solar_url = f"https://eco.mtk.nao.ac.jp/koyomi/yoko/{year}/rekiyou{str(year)[2:]}2.html.en"
        if year == 2028:
            solar_url = ("https://eco.mtk.nao.ac.jp/cgi-bin/koyomi/cande/phenomena_sy_en.cgi"
                         f"?year={year}&lst=9&phenom=50&cal=0&jg=1&dtm=0&dt=0"
                         "&body=0&body=1&coord=1&figure=0")
        moon = json.loads(read_source(moon_url, f"moon-{year}.json", args.cache_dir))
        if moon.get("year") != year or len(moon.get("phasedata", [])) != moon.get("numphases"):
            raise ValueError(f"Unexpected USNO response for {year}")
        entries = [entry for entry in moon["phasedata"] if entry["phase"] == "New Moon"]
        if len(entries) not in (12, 13):
            raise ValueError(f"Unexpected new-moon count for {year}")
        for entry in entries:
            hour, minute = map(int, entry["time"].split(":"))
            instant = datetime(entry["year"], entry["month"], entry["day"], hour, minute, tzinfo=timezone.utc)
            data["new_moons"].append({"utc": iso(instant), "source": moon_url})
        solar = read_source(solar_url, f"solar-{year}.html", args.cache_dir).decode("iso-8859-1")
        data["solar_markers"].extend(parse_solar(solar, year, solar_url))
        data["sources"].extend([
            {"url": moon_url, "publisher": "US Naval Observatory", "original_timezone": "UTC", "year": year},
            {"url": solar_url, "publisher": "National Astronomical Observatory of Japan", "original_timezone": "Japan Central Standard Time (UTC+09:00)", "year": year},
        ])
    for key in ("new_moons", "solar_markers"):
        data[key].sort(key=lambda event: event["utc"])
        if len({e["utc"] for e in data[key]}) != len(data[key]):
            raise ValueError(f"Duplicate times in {key}")
    destination = ROOT / "data" / "astronomy.json"
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print(f"Saved {len(data['new_moons'])} new moons and {len(data['solar_markers'])} solar markers.")


if __name__ == "__main__":
    main()
