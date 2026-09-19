/* Pure calendar functions. Inputs are published events, never average month lengths. */
(function (root) {
  "use strict";
  function upperBound(list, value, key = x => x) {
    let lo = 0, hi = list.length;
    while (lo < hi) {
      const mid = (lo + hi) >>> 1;
      if (key(list[mid]) <= value) lo = mid + 1;
      else hi = mid;
    }
    return lo;
  }
  function createCalendar(data) {
    const zone = data.location.timezone;
    const equinoxes = data.solar.filter(e => e[1] === 0);
    const min = equinoxes[0][0], max = equinoxes.at(-1)[0];
    const starts = data.months.map(m => data.sunsets[m[0]]);
    function phaseAt(at) {
      const index = upperBound(data.phases, at, e => e[0]) - 1;
      if (index < 0 || index >= data.phases.length - 1) throw new RangeError("No lunar phase data for this instant.");
      const left = data.phases[index], right = data.phases[index + 1];
      const fraction = (at - left[0]) / (right[0] - left[0]);
      return ((left[1] + fraction) / 4) % 1;
    }
    function phaseName(at) {
      const i = upperBound(data.phases, at, e => e[0]) - 1;
      if (i < 0 || i >= data.phases.length-1) throw new RangeError("No lunar phase data for this instant.");
      if (at - data.phases[i][0] < 60000) return ["New moon", "First quarter", "Full moon", "Last quarter"][data.phases[i][1]];
      return ["Waxing crescent", "Waxing gibbous", "Waning gibbous", "Waning crescent"][data.phases[i][1]];
    }
    function stateAt(at) {
      if (!Number.isFinite(at) || at < min || at >= max) throw new RangeError("This copy covers the 2025 vernal equinox through the 2028 vernal equinox.");
      const monthIndex = upperBound(starts, at) - 1;
      const month = data.months[monthIndex];
      const sunsetIndex = upperBound(data.sunsets, at) - 1;
      if (!month || sunsetIndex < month[0] || sunsetIndex >= month[1]) throw new RangeError("Incomplete local day data.");
      const yearIndex = upperBound(equinoxes, at, e => e[0]) - 1;
      const year = new Date(equinoxes[yearIndex][0]).getUTCFullYear();
      const solarIndex = upperBound(data.solar, at, e => e[0]) - 1;
      const nextPhase = data.phases[upperBound(data.phases, at, e => e[0])];
      return {
        at, monthIndex, name: month[2], day: sunsetIndex - month[0] + 1,
        totalDays: month[1] - month[0], monthStart: starts[monthIndex],
        monthEnd: data.sunsets[month[1]], newMoon: month[3],
        dayStart: data.sunsets[sunsetIndex], dayEnd: data.sunsets[sunsetIndex+1],
        year: `${year}–${year+1}`, phase: phaseAt(at), phaseName: phaseName(at),
        nextPhase, nextNewMoon: data.phases.find(e => e[0] > at && e[1] === 0),
        nextFullMoon: data.phases.find(e => e[0] > at && e[1] === 2),
        currentMarker: data.solar[solarIndex], nextMarker: data.solar[solarIndex+1],
      };
    }
    function dayInstant(monthIndex, day) {
      const month = data.months[monthIndex];
      if (!month || !Number.isInteger(day) || day < 1 || day > month[1]-month[0]) throw new RangeError("No such day in this month.");
      const start = data.sunsets[month[0]+day-1], end = data.sunsets[month[0]+day];
      // Midday within the sunset day; clamp only at a supported solar-year boundary.
      return Math.max(min, Math.min(max-1, (start+end)/2));
    }
    const partFormatter = new Intl.DateTimeFormat("en-US", {timeZone: zone, year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23"});
    function localParts(at) {
      return Object.fromEntries(partFormatter.formatToParts(new Date(at)).filter(p => p.type !== "literal").map(p => [p.type, Number(p.value)]));
    }
    function localDate(at) {
      const p = localParts(at);
      return `${p.year}-${String(p.month).padStart(2,"0")}-${String(p.day).padStart(2,"0")}`;
    }
    function fromLocalDate(date) {
      if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) throw new RangeError("Choose a valid date.");
      if (date < localDate(min) || date > localDate(max-1)) throw new RangeError("This date is outside the included calendar.");
      const [year, month, day] = date.split("-").map(Number);
      const target = Date.UTC(year, month-1, day, 12);
      let at = target;
      for (let i=0; i<3; i++) {
        const p = localParts(at);
        at += target - Date.UTC(p.year, p.month-1, p.day, p.hour, p.minute, p.second);
      }
      if (localDate(at) !== date) throw new RangeError("Choose a valid date.");
      return Math.max(min, Math.min(max-1, at));
    }
    return {data, zone, min, max, stateAt, phaseAt, phaseName, dayInstant, localParts, localDate, fromLocalDate};
  }
  const api = {createCalendar, upperBound};
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.DraiochtCalendar = api;
})(typeof window !== "undefined" ? window : globalThis);
