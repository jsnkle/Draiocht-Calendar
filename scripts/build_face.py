#!/usr/bin/env python3
"""Bundle the Draíocht face as one offline HTML file, using the calendar's data."""

import argparse
import base64
import json
from pathlib import Path

import build_calendars as calendar

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"


def face_data():
    astronomy, sunset_data = calendar.load(), calendar.load_sunsets()
    moons, sunsets, starts, boundaries, names = calendar.daily_model(astronomy, sunset_data)
    milliseconds = lambda at: round(at.timestamp()*1000)
    return {
        "location": sunset_data["location"],
        "retrieved": astronomy["retrieved_on"],
        "sunsets": [milliseconds(at) for at in sunsets],
        "months": [[starts[i], starts[i+1], names[i], milliseconds(moons[i])]
                   for i in range(len(moons)-1)],
        "solar": [[milliseconds(calendar.instant(e["utc"])), e["longitude"], e["name"]]
                  for e in astronomy["solar_markers"]],
        "phases": [[milliseconds(calendar.instant(e["utc"])),
                    ["New Moon", "First Quarter", "Full Moon", "Last Quarter"].index(e["phase"])]
                   for e in astronomy["lunar_phases"]],
    }


def bundle():
    content = (WEB / "template.html").read_text()
    replacements = {
        "/* FACE_CSS */": (WEB / "face.css").read_text(),
        "/* CALENDAR_JS */": (WEB / "calendar.js").read_text(),
        "/* FACE_JS */": (WEB / "face.js").read_text(),
        "/* MOON_JS */": (WEB / "moon.js").read_text(),
        "/* MOON_TEXTURE */": "window.DRAIOCHT_MOON_TEXTURE = " + json.dumps(
            "data:image/jpeg;base64," + base64.b64encode(
                (WEB / "assets" / "lroc-color-2k.jpg").read_bytes()).decode("ascii")) + ";",
        "/* FACE_DATA */": "window.DRAIOCHT_DATA = " + json.dumps(face_data(), ensure_ascii=False, separators=(",", ":")) + ";",
    }
    for placeholder, replacement in replacements.items():
        if content.count(placeholder) != 1:
            raise ValueError(f"Expected one {placeholder} in template")
        content = content.replace(placeholder, replacement)
    return content


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    destination = WEB / "index.html"
    content = bundle()
    if args.check:
        if not destination.exists() or destination.read_text() != content:
            raise SystemExit("web/index.html is out of date; run scripts/build_face.py")
    else:
        destination.write_text(content)
    print(f"{'Verified' if args.check else 'Wrote'} web/index.html ({len(content.encode()):,} bytes)")


if __name__ == "__main__":
    main()
