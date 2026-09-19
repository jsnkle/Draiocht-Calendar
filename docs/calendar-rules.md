# Calendar rules

These are the rules I'm using for Draíocht. The equinox year, new-moon months, sunset-to-sunset days, Idir-Ré, the seasonal Black Moon, and angular seasonal markers form its structure. The [month names](month-names.md) describe the solar cycle.

## The year

A year begins at the vernal equinox in the Northern Hemisphere and ends at the next vernal equinox. The boundary is the northward crossing of the celestial equator by the Sun's center. It is one event worldwide, displayed differently in different time zones. It does not generally coincide with exactly equal durations of daylight and darkness. [US Naval Observatory](https://aa.usno.navy.mil/faq/equinoxes).

The label **2026–2027** identifies the year beginning at the 2026 vernal equinox. These Gregorian year numbers are a reference convention, not a separate astronomical rule.

Use intervals that include their beginning and exclude their end. At the equinox instant, the new year has begun. Its duration is whatever time elapses until the next equinox, roughly 365¼ days, rather than a prescribed integer number of days.

## The month

A month begins with the **sunset-to-sunset day containing astronomical new moon**. The whole of that day is day 1, including the part before conjunction. The month ends when day 1 of the next month begins.

Astronomical new moon is the conjunction at which the Sun and Moon have the same apparent geocentric ecliptic longitude. The exact event identifies the day; it does not split that day into two dates. A lunation is the astronomical interval from one conjunction to the next, while my dated month consists of whole sunset-to-sunset days.

The average lunation is approximately 29.53 days, with natural variation. A new moon is ordinarily invisible; the first visible crescent appears later and depends on viewing conditions. Calculated conjunction and crescent sighting are different possible boundaries. Draíocht uses conjunction, while encouraging observation throughout the month. [NASA on lunar cycles](https://eclipse.gsfc.nasa.gov/help/moonorbit.html); [USNO on phases and crescent visibility](https://aa.usno.navy.mil/faq/crescent).

Published tables give event times to a stated precision. They are predictions based on astronomical models, not naked-eye observations of each event. The current reference calendars use times rounded to one minute.

## Idir-Ré

Idir-Ré is the lunar month containing the vernal equinox. Its opening portion belongs to the ending year; its remaining portion belongs to the new year. The lunar month and its day count continue across that boundary.

For example, in Orlando in 2026, Idir-Ré begins at sunset on March 18, listed as 19:36 EDT. The new moon occurs later that evening at 21:23. The year changes on March 20 at 10:46 EDT, during day 2 of Idir-Ré. The next month begins at sunset on April 16, listed as 19:52 EDT, because the following morning's new moon falls within that sunset-to-sunset day. [Reference calendar](../calendars/2026-2027.md).

The length of each portion varies. Even if conjunction and the equinox coincide, day 1 ordinarily began at the preceding sunset. If the equinox itself falls exactly at a month's opening sunset, that month has no portion in the ending year. Close but unequal events must remain distinct; rounding two times to the same minute does not establish physical simultaneity. A boundary case closer than the source precision requires better data.

I use **before equinox** and **after equinox** to distinguish the portions. The [naming notes](language-and-naming-research.md#the-two-parts-of-idir-ré) also explain *Críoch* and *Tús*, the ending and beginning labels from my earlier draft.

## Counting months and leap adjustments

Keep two spans distinct:

- **Solar year:** equinox to equinox.
- **Astronomical sequence:** the new moon associated with one Idir-Ré to the new moon associated with the next.

In the reference calendars, the second span contains twelve or thirteen whole lunations. The dated months begin at their respective day-1 sunsets. The solar year usually begins partway through one dated month and ends partway through another. Those partial months cannot simply be added together and called one complete lunar cycle.

In 2025–2026, thirteen lunations separate the Idir-Ré new moons; the solar year includes twelve complete dated months and two threshold portions in Orlando. In 2026–2027, twelve lunations separate the new moons; the solar year includes eleven complete dated months and two threshold portions. Neither solar year becomes 354 or 384 days long.

Draíocht has no fixed leap-day or leap-month schedule. The number of lunations follows the events. Ré Anann names a lunation identified by the Black Moon rule below; it does not create or insert a physical lunar cycle.

## Black Moon and Ré Anann

**A Black Moon is the third new moon in an astronomical season containing four new moons.** I chose this definition to identify **Ré Anann**, the lunar month whose day 1 contains that event.

Here, an astronomical season runs from an equinox or solstice to the next solstice or equinox. Count new-moon instants within that span, including its opening boundary and excluding its closing boundary. A new moon exactly at a boundary belongs to the season beginning there. The count uses these global events and is independent of the time zone used to display them.

In 2025, the season from the summer solstice to the autumnal equinox contains new moons on June 25, July 24, August 23, and September 21 in Orlando's time zone. August 23 is the third. Ré Anann begins at the preceding sunset on August 22, and the next month begins at sunset on September 20. [Reference calendar](../calendars/2025-2026.md).

This rule counts events within a season, not months within a Gregorian year. The [naming rules](month-names.md#assigning-names) describe how the other months fit around Ré Anann and how unusual arrangements are handled.

## Seasonal markers

The Sun's apparent geocentric ecliptic longitude, measured from the vernal equinox, defines the eight markers. Seasonal names refer to the Northern Hemisphere:

| Marker in this calendar | Longitude |
|---|---:|
| Vernal equinox | 0° |
| Beltane | 45° |
| Summer solstice | 90° |
| Lughnasadh | 135° |
| Autumnal equinox | 180° |
| Samhain | 225° |
| Winter solstice | 270° |
| Imbolc | 315° |

These are equal angular steps along the annual path, not equal intervals of time, daylight, or solar height above the horizon. Solar longitude is also used in the astronomical definition of solar terms. [Hong Kong Observatory](https://www.hko.gov.hk/en/gts/time/24solarterms.htm).

I use the four festival names for these exact positions. I haven't established that historical communities used the same calculations. The markers supply reference instants; [observance](natural-tuning.md) may extend to either side.

## Daily dates

**My day begins when the Sun has completely set and continues until the following sunset.** The astronomical new moon identifies day 1; the entire day containing it belongs to the new month.

1. Find the sunset-to-sunset day containing the new moon. That whole day is day 1, beginning at its opening sunset.
2. At each subsequent sunset, increase the day number by one.
3. When the sunset-to-sunset day containing the next new moon begins, change the month and reset to day 1.
4. At the equinox, change the year without resetting the month or day.

A new moon during the daylight hours belongs to the day that began at the previous evening's sunset. A new moon after sunset belongs to the day that has just begun. If conjunction occurs exactly at sunset, it belongs to the new day. Neither midnight nor conjunction changes the date within an already-begun day.

In Orlando in 2026, day 1 of Idir-Ré runs from March 18 at 19:36 EDT to March 19 at 19:36 EDT, containing the March 18 new moon at 21:23. Day 2 continues until sunset on March 20. At 10:45 EDT on March 20 it is still day 2 of the ending year; at the published 10:46 equinox boundary it is day 2 of 2026–2027.

By “completely set,” I mean the Sun's upper edge disappearing below the horizon. The reference tables use the standard calculated sunset, with a level horizon and average atmospheric refraction. Twilight continues afterward. [USNO's definitions](https://aa.usno.navy.mil/faq/RST_defs).

I begin each day at sunset, following the night-before-day reckoning Caesar describes among the Gauls. [*Gallic War* 6.18](https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Caesar/Gallic_War/6B%2A.html).

The worked calendars and [daily lookup](../data/README.md#look-up-a-date) use **Orlando, Florida**, with times displayed in **America/New_York**. Other locations need their own sunset times, not just a different clock display. Share the location when sharing numbered dates. The new-moon and equinox instants remain global; the sunset-to-sunset days are local.

## Place and continuing accuracy

The astronomical markers can be used anywhere. The seasonal language and Natural Tuning sequence come from a Northern Hemisphere, temperate-season perspective. Local climate and ecology shape how those markers are experienced.

Future event calculations can follow changes in the lunar and solar cycles without preserving today's average durations. Published tables still need refreshing, and source precision, time-zone rules, day conventions, and naming rules need maintenance. Following events avoids a fixed leap schedule; it does not make the whole calendar permanently free of design decisions.
