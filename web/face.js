(function () {
  "use strict";
  const $ = id => document.getElementById(id);
  const cal = DraiochtCalendar.createCalendar(window.DRAIOCHT_DATA);
  const NS = "http://www.w3.org/2000/svg";
  const moon = DraiochtMoon.createRenderer(window.DRAIOCHT_MOON_TEXTURE, $("moon-photo"), $("moon-status"));
  let selected = null, current = null, ringKey = "", lastTextMinute = -1;
  let corner = "season";
  try { corner = localStorage.getItem("draiocht-corner") || "season"; } catch (_) { /* Storage is optional on local files. */ }
  if (!["season", "reflection", "full"].includes(corner)) corner = "season";
  $("corner-choice").value = corner;
  const focus = {
    0: ["Begin growth. Tend what is taking shape.", "What needs care now?"],
    45: ["Take inventory. Make adjustments.", "What is working, and what needs to change?"],
    90: ["Take inventory. Choose where to continue.", "Where is further effort worthwhile?"],
    135: ["Harvest. Celebrate what you’ve accomplished.", "What has this work produced, and who helped?"],
    180: ["End projects. Share your progress.", "What can I close, share, or carry over?"],
    225: ["Begin reflection and ideation.", "What is ending, and what might come next?"],
    270: ["Choose which ideas to carry forward.", "What deserves my attention?"],
    315: ["Begin implementation.", "What small action would make this real?"],
  };
  const months = {"Idir-Ré":"Between-time", "Éirí":"Rising", "Neartú":"Strengthening", "Grian Thuaidh":"Northern Sun", "Iompú":"Turning", "Giorrú":"Shortening", "Cothromú":"Balancing", "Ísliú":"Lowering", "Doimhniú":"Deepening", "Grian Theas":"Southern Sun", "Filleadh":"Return", "Síneadh":"Lengthening", "Ré Anann":"Moon of Anu"};
  const format = (at, options) => new Intl.DateTimeFormat("en-US", {timeZone:cal.zone,...options}).format(new Date(at));
  const time = at => format(at, {hour:"numeric", minute:"2-digit"});
  const shortDate = at => format(at, {month:"short", day:"numeric"});
  const eventDate = at => `${shortDate(at)} · ${time(at)}`;
  const phaseLabels = ["New moon", "First quarter", "Full moon", "Last quarter"];
  function svg(tag, attrs, parent) {
    const el = document.createElementNS(NS, tag);
    for (const [key, value] of Object.entries(attrs)) el.setAttribute(key, value);
    if (parent) parent.appendChild(el);
    return el;
  }
  function point(cx, cy, radius, angle) {
    const a = angle*Math.PI/180;
    return [cx + radius*Math.sin(a), cy - radius*Math.cos(a)];
  }
  // Projected terminator, using an interpolated phase angle. No claim of sky orientation.
  function moonPath(cx, cy, radius, phase) {
    const waxing = phase <= .5, cosine = Math.cos(phase*2*Math.PI);
    const points = [];
    for (let i=0; i<=40; i++) {
      const y = -radius + 2*radius*i/40;
      const edge = Math.sqrt(Math.max(0, radius*radius-y*y));
      points.push([cx + (waxing ? edge : -edge), cy+y]);
    }
    for (let i=40; i>=0; i--) {
      const y = -radius + 2*radius*i/40;
      const edge = Math.sqrt(Math.max(0, radius*radius-y*y));
      points.push([cx + (waxing ? cosine : -cosine)*edge, cy+y]);
    }
    return points.map(([x,y],i) => `${i ? "L" : "M"}${x.toFixed(2)},${y.toFixed(2)}`).join(" ") + " Z";
  }
  function until(at, now, short = false) {
    let minutes = Math.max(0, Math.ceil((at-now)/60000));
    const days = Math.floor(minutes/1440); minutes %= 1440;
    const hours = Math.floor(minutes/60); minutes %= 60;
    if (short) return days ? `${days}d ${hours}h away` : `${hours}h ${minutes}m away`;
    return days ? `In ${days} ${days === 1 ? "day" : "days"}${hours ? `, ${hours}h` : ""}` : hours ? `In ${hours}h ${minutes}m` : minutes ? `In ${minutes} ${minutes === 1 ? "minute" : "minutes"}` : "Now";
  }
  function drawRing(state) {
    const key = `${state.monthIndex}:${state.day}`;
    if (key === ringKey) return;
    ringKey = key;
    $("day-ring").replaceChildren();
    for (let day=1; day<=state.totalDays; day++) {
      const angle = (day-state.day)*360/state.totalDays;
      const [x,y] = point(310,310,271,angle);
      const [mx,my] = point(310,310,233.5,angle);
      const [hx,hy] = point(310,310,251.5,angle);
      const i = cal.data.months[state.monthIndex][0]+day-1;
      const a = cal.data.sunsets[i], b = cal.data.sunsets[i+1];
      const available = b > cal.min && a < cal.max;
      const group = svg("g", {class:`day-slot${day===state.day ? " selected" : ""}`,role:"button",tabindex:available ? "0" : "-1","aria-disabled":String(!available),"aria-label":`${state.name}, day ${day}. Begins ${format(a,{month:"long",day:"numeric"})} at ${time(a)}.`,"data-day":day},$("day-ring"));
      svg("rect",{class:"slot-hit",x:hx-16,y:hy-35,width:32,height:70,rx:15,transform:`rotate(${angle} ${hx} ${hy})`,opacity:available?1:.3},group);
      const label = svg("text",{class:"day-number",x,y},group); label.textContent=String(day).padStart(2,"0");
      svg("circle",{cx:mx,cy:my,r:7.8,fill:"#302c40",stroke:"#51495f","stroke-width":.5},group);
      svg("path",{d:moonPath(mx,my,7.8,cal.phaseAt((a+b)/2)),fill:day===state.day?"#ecddff":"#b4a2cf",opacity:available?1:.35},group);
      if (available) {
        const select = () => explore(cal.dayInstant(state.monthIndex,day));
        group.addEventListener("click",select);
        group.addEventListener("keydown",event => {if(event.key==="Enter"||event.key===" "){event.preventDefault();select();$("day-ring").querySelector(`[data-day="${day}"]`).focus({preventScroll:true});}});
      }
    }
  }
  function seasonIcon(marker) {
    const icon = $("season-icon"); icon.replaceChildren();
    svg("circle", {cx:24,cy:24,r:13,fill:"none",stroke:"currentColor","stroke-width":.8,opacity:.6}, icon);
    for (let i=0;i<8;i++) {
      const [x,y]=point(24,24,19,i*45);
      svg("circle",{cx:x,cy:y,r:marker[1]===i*45?2.8:1.4,fill:"currentColor",opacity:marker[1]===i*45?1:.5},icon);
    }
    const [x,y]=point(24,24,13,marker[1]);
    svg("line",{x1:24,y1:24,x2:x,y2:y,stroke:"currentColor","stroke-width":1},icon);
    svg("circle",{cx:24,cy:24,r:2,fill:"currentColor"},icon);
  }
  function updateCorner(state) {
    if (corner === "full") {
      const event=state.nextFullMoon;
      $("corner-label").textContent="NEXT FULL MOON";
      $("season-name").textContent=shortDate(event[0]);
      $("season-date").textContent=`${time(event[0])} · ${until(event[0],state.at,true)}`;
      $("reflection").textContent="The next full-moon instant.";
      $("season-icon").innerHTML='<circle cx="24" cy="24" r="15" fill="currentColor" opacity=".8"/><circle cx="20" cy="20" r="6" fill="#161520" opacity=".18"/>';
    } else {
      const marker=corner==="reflection"?state.currentMarker:state.nextMarker;
      $("corner-label").textContent=corner==="reflection"?"NATURAL TUNING":"NEXT TURN OF THE YEAR";
      $("season-name").textContent=marker[2];
      $("season-date").textContent=corner==="reflection"?focus[marker[1]][0]:eventDate(marker[0]);
      $("reflection").textContent=focus[marker[1]][corner==="reflection"?1:0];
      seasonIcon(marker);
    }
  }
  function render(force = false) {
    const at=selected===null?Date.now():selected;
    try { current=cal.stateAt(at); }
    catch(error) {
      $("instrument").hidden=true;$("error").hidden=false;$("error-message").textContent=error.message;
      $("previous-day").disabled=true;$("next-day").disabled=true;return;
    }
    $("instrument").hidden=false;$("error").hidden=true;
    const state=current;
    const minute=Math.floor(at/60000);
    if (!force && minute===lastTextMinute) return;
    lastTextMinute=minute;
    drawRing(state);
    moon.draw(state.phase);
    $("small-moon").setAttribute("d",moonPath(24,24,16,state.phase));
    $("phase-name").textContent=state.phaseName;
    $("phase-next").textContent=`${phaseLabels[state.nextPhase[1]]} · ${shortDate(state.nextPhase[0])}`;
    $("month-name").textContent=state.name;
    $("month-translation").textContent=(months[state.name] || "").toUpperCase();
    $("civil-date").textContent=format(at,{month:"long",day:"numeric",year:"numeric"});
    $("clock-time").textContent=time(at);$("clock-time").dateTime=new Date(at).toISOString();
    $("next-moon-date").textContent=shortDate(state.nextNewMoon[0]);
    $("next-moon-time").textContent=`${time(state.nextNewMoon[0])} · astronomical conjunction`;
    $("next-moon-away").textContent=until(state.nextNewMoon[0],at);
    $("sunset-time").textContent=time(state.dayEnd);
    $("sunset-away").textContent=`${shortDate(state.dayEnd)} · ${until(state.dayEnd,at,true)}`;
    const next=state.dayEnd < cal.max?cal.stateAt(state.dayEnd):null;
    $("tomorrow-date").textContent=next?`${next.name} · day ${next.day} begins` : "The next sunset";
    $("date-picker").value=cal.localDate(at);
    $("live-status").classList.toggle("exploring",selected!==null);
    $("live-status").innerHTML=`<span></span>${selected===null?"LIVE IN ORLANDO":"EXPLORING · ORLANDO TIME"}`;
    $("now-button").classList.toggle("active",selected===null);
    $("now-button").setAttribute("aria-pressed",String(selected===null));
    $("previous-day").disabled=state.dayStart<=cal.min;
    $("next-day").disabled=state.dayEnd>=cal.max;
    $("dial").setAttribute("aria-label",`${state.name}, day ${state.day} of ${state.totalDays}, ${state.year}. ${state.phaseName}. ${time(at)} in Orlando.`);
    updateCorner(state);
  }
  function explore(at) {
    selected=at;render(true);
    if(current) $("announcement").textContent=`${current.name}, day ${current.day}. ${format(at,{month:"long",day:"numeric",year:"numeric"})}, ${time(at)} in Orlando.`;
  }
  function stepDay(delta) {
    if(!current)return;
    const i=DraiochtCalendar.upperBound(cal.data.sunsets,current.at)-1+delta;
    const start=cal.data.sunsets[i],end=cal.data.sunsets[i+1];
    if(start===undefined||end===undefined||end<=cal.min||start>=cal.max)return;
    // Preserve progress through a sunset day; local daylight-saving changes do not add days.
    const progress=(current.at-current.dayStart)/(current.dayEnd-current.dayStart);
    explore(Math.max(cal.min,Math.min(cal.max-1,start+(end-start)*progress)));
  }
  $("date-picker").min=cal.localDate(cal.min);$("date-picker").max=cal.localDate(cal.max-1);
  $("date-picker").addEventListener("change",()=>{
    if(!$("date-picker").value||!$("date-picker").checkValidity())return;
    explore(cal.fromLocalDate($("date-picker").value));
  });
  $("previous-day").addEventListener("click",()=>stepDay(-1));
  $("next-day").addEventListener("click",()=>stepDay(1));
  $("now-button").addEventListener("click",()=>{selected=null;render(true);$("announcement").textContent="Live clock resumed.";});
  $("explore-available").addEventListener("click",()=>explore(cal.min));
  $("corner-choice").addEventListener("change",()=>{
    corner=$("corner-choice").value;
    try {localStorage.setItem("draiocht-corner",corner);}catch(_){}
    if(current)updateCorner(current);
  });
  $("about-button").addEventListener("click",()=>$("about-dialog").showModal());
  $("close-about").addEventListener("click",()=>$("about-dialog").close());
  $("about-dialog").addEventListener("click",event=>{if(event.target===$("about-dialog")){const r=event.target.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)event.target.close();}});
  // Optional bookmark of an explicit timestamp, useful for comparing a particular observation.
  const bookmark=new URLSearchParams(location.search).get("at");
  if(bookmark)selected=Date.parse(bookmark);
  render(true);
  setInterval(()=>{if(selected===null)render();},1000);
  document.addEventListener("visibilitychange",()=>{if(!document.hidden)render(true);});
})();
