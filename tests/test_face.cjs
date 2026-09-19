const test = require('node:test');
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const {readFileSync} = require('node:fs');
const path = require('node:path');
const {createCalendar} = require('../web/calendar.js');
const root = path.resolve(__dirname, '..');
const reference = JSON.parse(execFileSync('python3', ['-c', `
import json, sys
from datetime import timedelta
sys.path.insert(0, 'scripts')
import build_face, build_calendars as calendar
from zoneinfo import ZoneInfo
data, sunsets = calendar.load(), calendar.load_sunsets()
zone = ZoneInfo('America/New_York')
events = [calendar.instant(e['utc']) for key in ('new_moons','solar_markers') for e in data[key]]
events += [calendar.instant(v) for v in ('2026-03-19T04:00Z','2026-11-01T05:30Z','2026-11-01T06:30Z')]
events += [calendar.instant(e['utc']) for e in sunsets['sunsets'][::13]]
first,last = calendar.year_bounds(data,2025)[0],calendar.year_bounds(data,2027)[1]
results=[]
for event in events:
    for offset in (-1,0,1):
        at=event+timedelta(seconds=offset)
        if first <= at < last:
            value=calendar.lookup(data,at,zone,sunsets)
            results.append([round(at.timestamp()*1000),value])
print(json.dumps({'data':build_face.face_data(),'results':results}))
`], {cwd:root, encoding:'utf8', maxBuffer:4*1024*1024}));
const cal = createCalendar(reference.data);

test('browser dates agree with Python around conjunctions, sunsets, seasonal markers, and DST', () => {
  assert.ok(reference.results.length > 300);
  for (const [at, expected] of reference.results) {
    const actual = cal.stateAt(at);
    assert.equal(actual.name,expected.month,new Date(at).toISOString());
    assert.equal(actual.day,expected.day);
    assert.equal(actual.year,expected.year);
    assert.equal(actual.dayStart,Date.parse(expected.day_start_utc));
    assert.equal(actual.dayEnd,Date.parse(expected.day_end_utc));
    assert.equal(actual.monthStart,Date.parse(expected.month_start_utc));
  }
});
test('phase illustrations pass through the published primary phases', () => {
  for (const [at, phase] of reference.data.phases.slice(0,-1)) assert.equal(cal.phaseAt(at),phase/4);
  assert.equal(cal.phaseName(Date.parse('2026-09-19T14:10Z')),'Waxing gibbous');
});
test('whole day 1 starts at sunset before both daytime and evening new moons', () => {
  assert.equal(cal.stateAt(Date.parse('2026-04-16T23:51:59Z')).name,'Idir-Ré');
  for (const value of ['2026-04-16T23:52Z','2026-04-17T11:51:59Z','2026-04-17T11:52Z']) {
    assert.equal(cal.stateAt(Date.parse(value)).name,'Éirí');
    assert.equal(cal.stateAt(Date.parse(value)).day,1);
  }
  assert.equal(cal.stateAt(Date.parse('2026-03-18T23:36Z')).day,1);
  assert.equal(cal.stateAt(Date.parse('2026-03-19T04:00Z')).day,1);
  assert.equal(cal.stateAt(Date.parse('2026-03-19T23:36Z')).day,2);
});
test('date picker noon is in Orlando across daylight saving, independent of host timezone', () => {
  assert.equal(cal.fromLocalDate('2026-03-07'),Date.parse('2026-03-07T17:00Z'));
  assert.equal(cal.fromLocalDate('2026-03-08'),Date.parse('2026-03-08T16:00Z'));
  assert.equal(cal.fromLocalDate('2026-11-01'),Date.parse('2026-11-01T17:00Z'));
  assert.throws(()=>cal.fromLocalDate('2026-02-30'),RangeError);
  assert.throws(()=>cal.fromLocalDate('2030-01-01'),RangeError);
});
test('ring selections retain their day, including partial solar-year coverage', () => {
  for (let i=0;i<cal.data.months.length;i++) {
    const month=cal.data.months[i];
    for(let day=1;day<=month[1]-month[0];day++) {
      const start=cal.data.sunsets[month[0]+day-1],end=cal.data.sunsets[month[0]+day];
      if(end<=cal.min || start>=cal.max)continue;
      const state=cal.stateAt(cal.dayInstant(i,day));
      assert.equal(state.monthIndex,i);assert.equal(state.day,day);
    }
  }
});
test('coverage is explicit and the single file is reproducible', () => {
  assert.throws(()=>cal.stateAt(cal.min-1),RangeError);
  assert.throws(()=>cal.stateAt(cal.max),RangeError);
  assert.throws(()=>cal.stateAt(NaN),RangeError);
  execFileSync('python3',['scripts/build_face.py','--check'],{cwd:root});
  const html=readFileSync(path.join(root,'web/index.html'),'utf8');
  assert.ok(!/<script[^>]+src=|<link[^>]+rel=["']stylesheet/.test(html));
  assert.ok(!html.includes('/* FACE_DATA */'));
});
