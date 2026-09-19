#!/usr/bin/env python3
"""Build the reference calendars, or look up an instant, from cached event times."""

import argparse
from bisect import bisect_left, bisect_right
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
ANCHORS = {0: "Idir-Ré", 90: "Grian Thuaidh", 180: "Cothromú", 270: "Grian Theas"}
BETWEEN = {0: ("Éirí", "Neartú"), 90: ("Iompú", "Giorrú"),
           180: ("Ísliú", "Doimhniú"), 270: ("Filleadh", "Síneadh")}
DISPLAY_ZONE = "America/New_York"


def instant(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("A UTC offset or Z is required; a date alone cannot resolve a transition.")
    return result.astimezone(timezone.utc)


def load():
    return json.loads((ROOT / "data" / "astronomy.json").read_text())


def load_sunsets(path=None):
    data = json.loads((path or ROOT / "data/sunsets-orlando.json").read_text())
    events = [instant(e["utc"]) for e in data["sunsets"]]
    if len(events) < 2 or events != sorted(set(events)):
        raise ValueError("Sunsets must be strictly ordered and unique")
    zone = ZoneInfo(data["location"]["timezone"])
    dates = [at.astimezone(zone).date() for at in events]
    if any(right-left != timedelta(days=1) for left, right in zip(dates, dates[1:])):
        raise ValueError("Sunset data must cover consecutive local dates; missing sunsets need an explicit convention")
    return data


def month_index(moons, at):
    index = bisect_right(moons, at) - 1
    if index < 0 or index >= len(moons) - 1:
        raise ValueError("Instant is outside the complete lunar intervals in the cached data.")
    return index


def assign_names(moons, solar, boundaries=None):
    boundaries = moons if boundaries is None else boundaries
    # An identifier survives changes in the naming vocabulary.
    names = {i: f"Lunation {start:%Y-%m-%d} UTC" for i, start in enumerate(moons[:-1])}
    quarters = sorted((instant(e["utc"]), e["longitude"]) for e in solar if e["longitude"] in ANCHORS)
    anchored = []
    for at, longitude in quarters:
        try:
            index = month_index(boundaries, at)
        except ValueError:
            continue
        if any(previous == index for _, _, previous in anchored):
            raise ValueError("Two quarter points in one lunation require a naming review.")
        names[index] = ANCHORS[longitude]
        anchored.append((at, longitude, index))
    for left, right in zip(anchored, anchored[1:]):
        season_start, longitude, start = left
        season_end, next_longitude, end = right
        if next_longitude != (longitude + 90) % 360:
            raise ValueError("Missing quarter point in solar data")
        # Count conjunctions in [season_start, season_end), not the number
        # of months between anchors: they differ at coincident boundaries.
        season = range(bisect_left(moons, season_start), bisect_left(moons, season_end))
        black_moon = season[2] if len(season) == 4 else None
        if black_moon is not None:
            if not start < black_moon < end:
                raise ValueError("Black Moon overlaps a quarter-point month; naming review required.")
            names[black_moon] = "Ré Anann"
        gap = [index for index in range(start + 1, end) if index != black_moon]
        # Only the common arrangements have settled working names. Never
        # drop a real lunation or invent an exceptional name to fill a pattern.
        if len(gap) == 2:
            for index, name in zip(gap, BETWEEN[longitude]):
                names[index] = name
    return names


def model(data):
    moons = [instant(e["utc"]) for e in data["new_moons"]]
    if moons != sorted(set(moons)):
        raise ValueError("New moons must be strictly ordered and unique")
    return moons, assign_names(moons, data["solar_markers"])


def year_bounds(data, year):
    equinoxes = {instant(e["utc"]).year: instant(e["utc"])
                for e in data["solar_markers"] if e["longitude"] == 0}
    try:
        return equinoxes[year], equinoxes[year + 1]
    except KeyError as error:
        raise ValueError("Both bounding vernal equinoxes are required") from error


def day_index(sunsets, at):
    index = bisect_right(sunsets, at) - 1
    if index < 0 or index >= len(sunsets)-1:
        raise ValueError("Sunset data must bracket the requested instant")
    return index


def daily_model(data, sunset_data):
    moons, _ = model(data)
    sunsets = [instant(e["utc"]) for e in sunset_data["sunsets"]]
    starts = [day_index(sunsets, moon) for moon in moons]
    boundaries = [sunsets[index] for index in starts]
    names = assign_names(moons, data["solar_markers"], boundaries)
    return moons, sunsets, starts, boundaries, names


def lookup(data, at, zone, sunset_data=None):
    sunset_data = load_sunsets() if sunset_data is None else sunset_data
    moons, sunsets, starts, boundaries, names = daily_model(data, sunset_data)
    index = month_index(boundaries, at)
    current_day = day_index(sunsets, at)
    year = at.year
    equinox = next((instant(e["utc"]) for e in data["solar_markers"]
                    if e["longitude"] == 0 and instant(e["utc"]).year == year), None)
    if equinox is None:
        raise ValueError("No vernal equinox data for this date")
    if at < equinox:
        year -= 1
    left, right = year_bounds(data, year)
    if not left <= at < right:
        raise ValueError("No complete solar year for this instant")
    section = None
    for event in data["solar_markers"]:
        boundary = instant(event["utc"])
        if event["longitude"] == 0 and boundaries[index] <= boundary < boundaries[index + 1]:
            section = "before equinox" if at < boundary else "after equinox"
    return {"year": f"{year}–{year + 1}", "month": names[index],
            "day": current_day-starts[index]+1, "threshold_section": section,
            "day_start_utc": sunsets[current_day].isoformat(),
            "day_end_utc": sunsets[current_day+1].isoformat(),
            "month_start_utc": boundaries[index].isoformat(),
            "month_end_utc": boundaries[index+1].isoformat(),
            "month_new_moon_utc": moons[index].isoformat(),
            "location": sunset_data["location"], "display_timezone": str(zone),
            "day_start_local": stamp(sunsets[current_day], zone),
            "day_end_local": stamp(sunsets[current_day+1], zone)}


def stamp(at, zone):
    return at.astimezone(zone).strftime("%Y-%m-%d %H:%M %Z")


def duration(delta):
    minutes = round(delta.total_seconds() / 60)
    days, minutes = divmod(minutes, 1440)
    hours, minutes = divmod(minutes, 60)
    return f"{days}d {hours}h {minutes}m"


def render_year(data, year, zone, sunset_data=None):
    sunset_data = load_sunsets() if sunset_data is None else sunset_data
    moons, sunsets, starts, boundaries, names = daily_model(data, sunset_data)
    start, end = year_bounds(data, year)
    first, last = month_index(boundaries, start), month_index(boundaries, end)
    covered = [i for i in range(first, last + 1) if boundaries[i] < end and boundaries[i + 1] > start]
    full = sum(start <= boundaries[i] and boundaries[i + 1] <= end for i in covered)
    total = sum((min(boundaries[i + 1], end) - max(boundaries[i], start)).total_seconds() for i in covered)
    if total != (end - start).total_seconds():
        raise ValueError("Dated months do not exactly cover the solar year")
    lines = [f"# Draíocht {year}–{year + 1}", "",
             f"The year runs from the vernal equinox in the Northern Hemisphere on **{stamp(start, zone)}** to the next on **{stamp(end, zone)}**: {duration(end - start)} at the published precision.", "",
             f"Daily dates use **{sunset_data['location']['name']}** (28.54° N, 81.38° W). Times use **{zone}**, including daylight-saving changes. A day begins when the Sun has completely set. The whole sunset-to-sunset day containing a new moon is day 1 of its month.", "",
             f"There are **{last - first} complete lunations between the new moons associated with the opening and closing Idir-Ré**. The solar year overlaps {len(covered)} dated lunar months, of which {full} are wholly inside it. The remaining coverage comes from the threshold portions.", "",
             "## Lunar months", "",
             "The [month guide](../docs/month-names.md) explains the names and their place in the solar cycle. Both threshold months are shown in full. Numbered days count sunset-to-sunset spans; they are not fixed 24-hour units. The new-moon column records the astronomical event within day 1.", "",
             "| Month | Day 1 begins at sunset | Astronomical new moon | Next month begins at sunset | Numbered days |",
             "|---|---|---|---|---|"]
    for i in covered:
        lines.append(f"| {names[i]} | {stamp(boundaries[i], zone)} | {stamp(moons[i], zone)} | {stamp(boundaries[i+1], zone)} | {starts[i+1]-starts[i]} |")
    lines.extend(["", "## Seasonal markers", "",
                  "These are reference instants, with seasonal names referring to the Northern Hemisphere. Gatherings and personal observances may take place around them; see [Natural Tuning](../docs/natural-tuning.md). I use the four festival names for the angular markers shown here.", "",
                  "| Marker | Solar longitude | Local time | Lunar month |", "|---|---:|---|---|"])
    for event in data["solar_markers"]:
        at = instant(event["utc"])
        if start <= at < end:
            lines.append(f"| {event['name']} | {event['longitude']}° | {stamp(at, zone)} | {names[month_index(boundaries, at)]} |")
    lines.extend(["", f"The next year begins at the vernal equinox on **{stamp(end, zone)}**, within Idir-Ré.", "",
                  "## Daily use", "",
                  "The month changes at the sunset beginning its day 1, before or at the new moon. Each following sunset increases the day number until the next month's day 1. Midnight and conjunction do not split the day. The equinox changes the year without resetting the month or its day number. See [daily dates](../docs/calendar-rules.md#daily-dates).", "",
                  "## Sources", "",
                  f"Generated from [cached observatory times](../data/astronomy.json), retrieved {data['retrieved_on']}. New moons: US Naval Observatory, UTC. Solar positions: National Astronomical Observatory of Japan, converted from Japan Central Standard Time. Individual source URLs are retained with every event. Published times are rounded to a minute; their display is not a claim of second-level accuracy.", "",
                  f"[Orlando sunsets](../data/sunsets-orlando.json) come from USNO, retrieved {sunset_data['retrieved_on']}. They predict the Sun's upper edge meeting a level horizon with standard refraction. Terrain and atmospheric conditions can shift the observed sunset. These daily dates apply to Orlando; another location needs its own sunsets.", "",
                  "[Data and regeneration](../data/README.md) · [Calendar rules](../docs/calendar-rules.md) · [Project introduction](../README.md)", ""])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check reference files without rewriting them")
    parser.add_argument("--at", help="Look up an ISO timestamp with an explicit offset or Z")
    parser.add_argument("--timezone", default=DISPLAY_ZONE)
    parser.add_argument("--sunsets", type=Path, help="Local sunset JSON for --at; defaults to Orlando")
    args = parser.parse_args()
    data, zone = load(), ZoneInfo(args.timezone)
    if args.at:
        print(json.dumps(lookup(data, instant(args.at), zone, load_sunsets(args.sunsets)), ensure_ascii=False, indent=2))
        return
    if args.timezone != DISPLAY_ZONE:
        parser.error("Reference files use America/New_York; --timezone is available for --at lookups")
    if args.sunsets:
        parser.error("Reference files use Orlando; --sunsets is available for --at lookups")
    destination = ROOT / "calendars"
    if not args.check:
        destination.mkdir(exist_ok=True)
    for year in (2025, 2026, 2027):
        path = destination / f"{year}-{year+1}.md"
        content = render_year(data, year, zone)
        if args.check:
            if not path.exists() or path.read_text() != content:
                raise SystemExit(f"Out of date: {path.relative_to(ROOT)}")
        else:
            path.write_text(content)
        print(f"{'Verified' if args.check else 'Wrote'} {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
