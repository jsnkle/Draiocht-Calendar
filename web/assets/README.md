# Lunar surface imagery

`lroc-color-2k.jpg` is the unmodified 2048 × 1024 JPEG from NASA's [CGI Moon Kit](https://svs.gsfc.nasa.gov/4720/), downloaded September 19, 2026.

- [Original file](https://svs.gsfc.nasa.gov/vis/a000000/a004700/a004720/lroc_color_2k.jpg)
- Credit: **NASA's Scientific Visualization Studio**. Visualization by Ernie Wright (USRA); science by Noah Petro (NASA/GSFC). Surface imagery comes from Lunar Reconnaissance Orbiter / LROC data.
- NASA SVS makes its visualizations [public domain unless otherwise noted](https://svs.gsfc.nasa.gov/help/). This asset has no separate restriction listed.

The map contains real lunar surface imagery, with NASA's color adjustments and polar infilling. The browser projects it onto a sphere and applies approximate lighting for the displayed lunar phase. It is not a live photograph. Libration, terrain shadows, local sky tilt, and eclipses are not modeled. A faint night-side contribution keeps the disc visible; it is not a prediction of earthshine brightness.

The build script embeds the JPEG in `web/index.html`, so no separate image download is needed at runtime.
