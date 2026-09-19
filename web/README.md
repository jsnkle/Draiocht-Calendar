# Draíocht moon face

**[Open the hosted calendar](https://jsnkle.github.io/Draiocht-Calendar/)** on GitHub Pages.

Open **index.html** in a browser. It is a self-contained file: the styles, JavaScript, lunar imagery, and astronomical data are embedded, so it works from your computer without a server or internet connection. To put it online, upload that one file to a static web host.

The face uses the calendar's existing month names and Orlando sunset rules. It shows a lunar-day ring around the Moon, the month name and translation, the next new moon, and the next sunset. The civil date and digital time appear beneath the ring. Choose a day on the ring, use the arrows, or choose a Gregorian date to explore. **Now** returns to the live clock. Dates and times always use Orlando time, regardless of your computer's timezone.

The lower-left corner defaults to the next seasonal marker with its Natural Tuning focus. The selector also offers the current reflection prompt or the next full moon. Your choice stays in this browser when local storage is available.

Choosing a Gregorian date opens noon in Orlando. A lunar date can change later on that same Gregorian date, at sunset.

## Data and scope

This copy supports the 2025 vernal equinox through the 2028 vernal equinox. Unsupported dates show a coverage message. The source tables extend through Gregorian 2028 to bracket the closing lunar months; the complete solar-year coverage ends at the vernal equinox of 2028.

The central Moon uses real surface imagery from [NASA's Scientific Visualization Studio](https://svs.gsfc.nasa.gov/4720/), projected onto a sphere and lit for the phase interpolated between published USNO new, quarter, and full-moon instants. Its lighting is approximate, with lunar north up; it does not model libration, terrain shadows, local sky tilt, or eclipses. See the [image source and credits](assets/README.md). The small phase symbols around the ring remain schematic. Event times and sunset boundaries use the cached observatory records at their published minute precision. See [data and sources](../data/README.md).

Orlando is the reference location, at 28.54° N, 81.38° W. This version has no location selector. It makes no background network requests and needs no API keys or third-party libraries.

## Development

Edit `template.html`, `face.css`, `face.js`, `moon.js`, or `calendar.js`, then run from the repository root:

```sh
python3 scripts/build_face.py
python3 scripts/build_face.py --check
node --test tests/test_face.cjs
```

The builder uses the same Python calendar rules that generate the Markdown calendars, then embeds compact month boundaries, sunsets, primary Moon phases, and solar markers. Refresh the source data with the commands in the [data guide](../data/README.md), then rebuild both the calendars and this face.

For a local HTTP preview, run:

```sh
python3 -m http.server 8765 --bind 127.0.0.1 --directory web
```

Open `http://localhost:8765/`. An optional `?at=2026-09-19T14%3A10%3A00Z` query opens a particular instant in exploration mode. Without it, the clock is live.

## Publishing updates

GitHub Pages publishes the self-contained `index.html` through the [publishing workflow](../.github/workflows/pages.yml). Each push to `main` runs the Python and JavaScript tests and verifies that the generated calendars and browser file are current before publishing. Rebuild `web/index.html` after editing its sources and include it in the same commit.

The workflow can also be started manually from the repository's Actions tab. Deployments run only from `main`. Repository Settings → Pages uses **GitHub Actions** as the publishing source. The published artifact contains only the bundled calendar page, including its embedded data, imagery, and credits.
