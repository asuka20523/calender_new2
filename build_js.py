js = r"""
const LS_KEY="calendarAppDataV2";
const DEF_COLORS=(()=>{
  const hx=["#e57373","#f06292","#ba68c8","#9575cd","#7986cb","#64b5f6","#4fc3f7","#4dd0e1","#4db6ac","#81c784","#aed581","#dce775","#fff176","#ffd54f","#ffb74d","#ff8a65","#a1887f","#90a4ae","#ef5350","#ec407a","#ab47bc","#7e57c2","#5c6bc0","#42a5f5","#29b6f6","#26c6da","#26a69a","#66bb6a","#9ccc65","#d4e157"];
  return hx.map((h,i)=>({id:"c"+i,hex:h,name:"",custom:false}));
})();
function loadData(){try{const r=localStorage.getItem(LS_KEY);if(r)return JSON.parse(r);}catch(e){}return{events:[],colors:DEF_COLORS,templates:[],history:[],monthScrollMode:"vertical"};}
let DATA=loadData();
// backward compat: ensure all colors have custom flag
DATA.colors.forEach(c=>{if(c.custom===undefined)c.custom=false;});
if(!DATA.monthScrollMode)DATA.monthScrollMode="vertical";
if(!DATA.pillFontSize)DATA.pillFontSize=3;
if(!DATA.pillFontWeight)DATA.pillFontWeight=3;
if(!DATA.pillTextColor)DATA.pillTextColor="black";
if(!DATA.colorUsage)DATA.colorUsage={};
function save(){localStorage.setItem(LS_KEY,JSON.stringify(DATA));}
function trackColor(colorId){DATA.colorUsage[colorId]=(DATA.colorUsage[colorId]||0)+1;save();}
function sortedColors(){return [...DATA.colors].sort((a,b)=>((DATA.colorUsage[b.id]||0)-(DATA.colorUsage[a.id]||0)));}

const todayStr=fmtDate(new Date());
let state={tab:"month",cursor:new Date(),selectedDate:todayStr,editing:null};
function fmtDate(d){return d.getFullYear()+"-"+String(d.getMonth()+1).padStart(2,"0")+"-"+String(d.getDate()).padStart(2,"0");}
function parseDate(s){const[y,m,d]=s.split("-").map(Number);return new Date(y,m-1,d);}
function startOfWeek(d){const n=new Date(d);n.setDate(n.getDate()-n.getDay());return n;}

const _hc={};
function getHolidays(year){
  if(_hc[year])return _hc[year];
  const h=new Set();
  const a=(m,d)=>h.add(year+"-"+String(m).padStart(2,"0")+"-"+String(d).padStart(2,"0"));
  const nw=(m,wd,n)=>{let d=new Date(year,m-1,1),c=0;for(let i=0;i<31;i++){if(d.getDay()===wd&&++c===n)return d.getDate();d.setDate(d.getDate()+1);}};
  a(1,1);a(1,nw(1,1,2));a(2,11);a(2,23);
  a(3,Math.floor(20.8431+0.242194*(year-1980)-Math.floor((year-1980)/4)));
  a(4,29);a(5,3);a(5,4);a(5,5);a(7,nw(7,1,3));a(8,11);a(9,nw(9,1,3));
  a(9,Math.floor(23.2488+0.242194*(year-1980)-Math.floor((year-1980)/4)));
  a(10,nw(10,1,2));a(11,3);a(11,23);
  [...h].forEach(ds=>{const d=parseDate(ds);if(d.getDay()===0){const n=new Date(d);n.setDate(n.getDate()+1);h.add(fmtDate(n));}});
  return _hc[year]=h;
}
function isHoliday(ds){return getHolidays(parseInt(ds)).has(ds);}
function colorOf(id){return DATA.colors.find(c=>c.id===id)||DATA.colors[0];}
function eventsForDate(ds,excludeIds=new Set()){
  const d=parseDate(ds);
  return DATA.events.filter(ev=>!excludeIds.has(ev.id)&&matchDate(ev,d)).sort((a,b)=>(a.time||"99:99").localeCompare(b.time||"99:99"))
    .map(ev=>{if(ev.repeat==="none")return ev;const c=Object.assign({},ev);c.done=(ev.doneDates||[]).includes(ds);return c;});
}
function matchDate(ev,d){
  const ed=parseDate(ev.date);
  if(ev.repeat==="none"){
    if(ev.endDate&&ev.endDate>ev.date){const ds=fmtDate(d);return ds>=ev.date&&ds<=ev.endDate;}
    return ev.date===fmtDate(d);
  }
  if(d<ed)return false;
  if(ev.repeat==="daily")return true;
  if(ev.repeat==="weekly")return d.getDay()===ed.getDay();
  if(ev.repeat==="monthly")return d.getDate()===ed.getDate();
  if(ev.repeat==="yearly")return d.getDate()===ed.getDate()&&d.getMonth()===ed.getMonth();
  return false;
}
function getSpanEvents(rowDates){
  const rowStart=rowDates[0],rowEnd=rowDates[6];
  const rs=fmtDate(rowStart),re=fmtDate(rowEnd);
  const result=[];
  DATA.events.forEach(ev=>{
    if(!ev.endDate||ev.endDate<=ev.date)return;
    if(ev.endDate<rs||ev.date>re)return;
    const colStart=Math.max(0,Math.round((parseDate(ev.date)-rowStart)/86400000));
    const colEnd=Math.min(6,Math.round((parseDate(ev.endDate)-rowStart)/86400000));
    const contLeft=ev.date<rs;
    const contRight=ev.endDate>re;
    result.push({ev,colStart,colEnd,contLeft,contRight});
  });
  return result;
}
function assignTracks(spanEvents){
  const tracks=[];
  spanEvents.sort((a,b)=>a.colStart-b.colStart);
  spanEvents.forEach(se=>{
    let placed=false;
    for(let t=0;t<tracks.length;t++){
      const last=tracks[t][tracks[t].length-1];
      if(last.colEnd<se.colStart){tracks[t].push(se);placed=true;break;}
    }
    if(!placed)tracks.push([se]);
  });
  return tracks;
}

const app=document.getElementById("app");
function render(){
  app.innerHTML="";
  if(state.tab==="settings"){app.appendChild(buildSettingsHeader());app.appendChild(buildSettingsBody());app.appendChild(buildBottomNav());return;}
  if(state.tab==="task"){app.appendChild(buildHeader(false));app.appendChild(buildTaskBody());app.appendChild(buildBottomNav());return;}
  app.appendChild(buildHeader(true));
  app.appendChild(buildWeekrow());
  app.appendChild(buildCalArea());
  app.appendChild(buildDetailPanel());
  app.appendChild(buildBottomNav());
}

function buildHeader(showNav){
  const h=document.createElement("div");h.className="header";
  const left=document.createElement("button");left.className="iconbtn";left.textContent="‹";left.onclick=()=>shiftCursor(-1);
  const title=document.createElement("div");title.className="title";
  title.textContent=state.cursor.getFullYear()+"年"+(state.cursor.getMonth()+1)+"月";
  const right=document.createElement("button");right.className="iconbtn";right.textContent="›";right.onclick=()=>shiftCursor(1);
  const todayBtn=document.createElement("button");todayBtn.className="todayBtn";todayBtn.textContent="今日";
  todayBtn.onclick=()=>{state.cursor=new Date();state.selectedDate=todayStr;render();};
  const nav=document.createElement("div");nav.className="nav";
  if(showNav)nav.append(left,title,right);else nav.appendChild(title);
  h.append(nav,todayBtn);return h;
}
function shiftCursor(dir){
  const c=new Date(state.cursor);
  if(state.tab==="week")c.setDate(c.getDate()+dir*7);
  else c.setMonth(c.getMonth()+dir);
  state.cursor=c;
  if(DATA.monthScrollMode==="vertical"&&state.tab==="month"){
    const wrap=app.querySelector(".calwrap");
    if(wrap){const sec=wrap.querySelector('[data-y="'+c.getFullYear()+'"][data-m="'+c.getMonth()+'"]');
    if(sec){wrap.scrollTo({top:sec.offsetTop,behavior:"smooth"});const t=document.querySelector(".header .title");if(t)t.textContent=c.getFullYear()+"年"+(c.getMonth()+1)+"月";return;}}
  }
  render();
}
function buildWeekrow(){
  const wr=document.createElement("div");wr.className="weekrow";
  ["日","月","火","水","木","金","土"].forEach((w,i)=>{
    const d=document.createElement("div");d.textContent=w;
    if(i===0)d.className="sun";if(i===6)d.className="sat";wr.appendChild(d);
  });return wr;
}

function buildCalArea(){
  const wrap=document.createElement("div");wrap.className="calwrap";
  if(state.tab==="week"){wrap.appendChild(buildWeekStrip());return wrap;}
  if(DATA.monthScrollMode==="vertical"){wrap.classList.add("vscroll");buildVerticalScroll(wrap);}
  else buildHorizontalMonth(wrap);
  return wrap;
}
function buildVerticalScroll(wrap){
  const now=new Date();const BEFORE=6,AFTER=18;const sections=[];
  for(let i=-BEFORE;i<=AFTER;i++){
    const anchor=new Date(now.getFullYear(),now.getMonth()+i,1);
    const sec=document.createElement("div");sec.className="monthSection";
    sec.dataset.y=anchor.getFullYear();sec.dataset.m=anchor.getMonth();
    const lbl=document.createElement("div");lbl.className="monthLabel";
    lbl.textContent=anchor.getFullYear()+"年"+(anchor.getMonth()+1)+"月";
    sec.appendChild(lbl);sec.appendChild(buildMonthGrid(anchor,true));
    wrap.appendChild(sec);sections.push(sec);
  }
  requestAnimationFrame(()=>{
    const cy=state.cursor.getFullYear(),cm=state.cursor.getMonth();
    const cur=wrap.querySelector('[data-y="'+cy+'"][data-m="'+cm+'"]');
    if(cur)wrap.scrollTop=cur.offsetTop-2;
  });
  const obs=new IntersectionObserver(entries=>{
    entries.forEach(e=>{
      if(e.isIntersecting){
        const y=parseInt(e.target.dataset.y),m=parseInt(e.target.dataset.m);
        state.cursor=new Date(y,m,1);
        const t=document.querySelector(".header .title");if(t)t.textContent=y+"年"+(m+1)+"月";
      }
    });
  },{root:wrap,threshold:0.15});
  sections.forEach(s=>obs.observe(s));
}
function buildHorizontalMonth(wrap){
  const pager=document.createElement("div");pager.className="monthPager";
  pager.appendChild(buildMonthGrid(state.cursor,false));
  wrap.appendChild(pager);
  let sX=0,sY=0,mv=false;
  wrap.addEventListener("touchstart",e=>{sX=e.touches[0].clientX;sY=e.touches[0].clientY;mv=false;});
  wrap.addEventListener("touchmove",()=>{mv=true;});
  wrap.addEventListener("touchend",e=>{if(!mv)return;const dx=e.changedTouches[0].clientX-sX,dy=e.changedTouches[0].clientY-sY;if(Math.abs(dx)>50&&Math.abs(dx)>Math.abs(dy))shiftCursor(dx<0?1:-1);});
}

function buildMonthGrid(anchor,compact){
  const container=document.createElement("div");
  container.className=compact?"monthPageCompact":"monthPage";
  const year=anchor.getFullYear(),month=anchor.getMonth();
  const first=new Date(year,month,1);
  const gs=startOfWeek(first);
  const lastDate=new Date(year,month+1,0).getDate();
  const rows=Math.ceil((first.getDay()+lastDate)/7);
  if(!compact)container.style.gridTemplateRows="repeat("+rows+",1fr)";
  for(let r=0;r<rows;r++){
    const rowDates=[];
    for(let c=0;c<7;c++){const d=new Date(gs);d.setDate(gs.getDate()+r*7+c);rowDates.push(d);}
    const wrapper=document.createElement("div");wrapper.className="weekRowWrapper";
    const spanEvents=getSpanEvents(rowDates);
    const spanIds=new Set(spanEvents.map(s=>s.ev.id));
    if(spanEvents.length>0){
      const tracks=assignTracks(spanEvents);
      tracks.forEach(track=>{
        const layer=document.createElement("div");layer.className="spanLayer";
        track.forEach(({ev,colStart,colEnd,contLeft,contRight})=>{
          const bar=document.createElement("div");bar.className="spanBar";
          const cls=contLeft&&contRight?"continues-both":contLeft?"continues-left":contRight?"continues-right":"";
          if(cls)bar.classList.add(cls);
          bar.style.gridColumn=(colStart+1)+"/"+(colEnd+2);
          const col=colorOf(ev.colorId);
          bar.style.background=col.hex+"44";
          bar.style.color=DATA.pillTextColor==="white"?"#fff":"#000";
          const FWEIGHTS=[400,500,600,700,800];
          bar.style.fontWeight=FWEIGHTS[(DATA.pillFontWeight||3)-1];
          if(contLeft)bar.textContent="◁ "+ev.title;
          else if(contRight)bar.textContent=ev.title+" ▷";
          else bar.textContent=ev.title;
          bar.onclick=()=>openForm(ev);
          layer.appendChild(bar);
        });
        wrapper.appendChild(layer);
      });
    }
    const rowEl=document.createElement("div");rowEl.className="weekRowG";
    rowDates.forEach(d=>{rowEl.appendChild(buildCell(d,d.getMonth()!==month,spanIds));});
    wrapper.appendChild(rowEl);
    container.appendChild(wrapper);
  }
  return container;
}

function buildCell(d,other,spanIds=new Set()){
  const ds=fmtDate(d);
  const cell=document.createElement("div");cell.className="cell";
  if(other)cell.classList.add("othermonth");
  const hol=isHoliday(ds);
  if(d.getDay()===0||hol)cell.classList.add("sunday");
  if(d.getDay()===6)cell.classList.add("saturday");
  if(ds===todayStr)cell.classList.add("today");
  if(ds===state.selectedDate)cell.classList.add("selected");
  const num=document.createElement("div");num.className="datenum";num.textContent=d.getDate();
  cell.appendChild(num);
  const FSIZES=[7,8,9,10,11],FWEIGHTS=[400,500,600,700,800];
  const pFS=FSIZES[(DATA.pillFontSize||3)-1]+"px";
  const pFW=FWEIGHTS[(DATA.pillFontWeight||3)-1];
  const pFC=DATA.pillTextColor==="white"?"#fff":"#000";
  const items=eventsForDate(ds,spanIds);
  items.slice(0,4).forEach(ev=>{
    const p=document.createElement("div");
    p.className="pill"+(ev.type==="task"?" task":"")+(ev.done?" done":"");
    const col=colorOf(ev.colorId);
    p.style.background=col.hex+"33";p.style.borderColor=col.hex+"66";
    p.style.fontSize=pFS;p.style.fontWeight=pFW;p.style.color=pFC;
    p.textContent=(ev.type==="task"?"☐ ":"")+ev.title;
    cell.appendChild(p);
  });
  if(items.length>4){
    const corner=document.createElement("div");corner.className="moreCorner";
    const triBg=document.createElement("div");triBg.className="moreTriBg";
    const mNum=document.createElement("div");mNum.className="moreNum";mNum.textContent="+"+(items.length-4);
    corner.append(triBg,mNum);cell.appendChild(corner);
  }
  cell.onclick=()=>{
    state.selectedDate=ds;state.cursor=new Date(d.getFullYear(),d.getMonth(),1);
    if(DATA.monthScrollMode==="vertical"&&state.tab==="month"){
      app.querySelectorAll(".cell.selected").forEach(c=>c.classList.remove("selected"));
      cell.classList.add("selected");
      const panel=app.querySelector(".detailPanel");
      if(panel)panel.replaceWith(buildDetailPanel());
    }else{render();}
  };
  return cell;
}

function buildWeekStrip(){
  const outer=document.createElement("div");outer.style.height="100%";
  const wg=document.createElement("div");wg.style.cssText="display:flex;height:100%;overflow-x:auto;scroll-snap-type:x mandatory;";
  for(let off=-1;off<=1;off++){
    const anchor=new Date(state.cursor);anchor.setDate(anchor.getDate()+off*7);
    const page=document.createElement("div");page.style.cssText="min-width:100%;scroll-snap-align:start;display:grid;grid-template-columns:repeat(7,1fr);height:100%;";
    const ws=startOfWeek(anchor);
    for(let i=0;i<7;i++){const d=new Date(ws);d.setDate(ws.getDate()+i);page.appendChild(buildCell(d,false));}
    wg.appendChild(page);
  }
  outer.appendChild(wg);
  requestAnimationFrame(()=>{wg.scrollLeft=wg.clientWidth;});
  wg.addEventListener("touchend",e=>{
    if(wg.scrollLeft<wg.clientWidth*0.4){state.cursor.setDate(state.cursor.getDate()-7);render();}
    else if(wg.scrollLeft>wg.clientWidth*1.6){state.cursor.setDate(state.cursor.getDate()+7);render();}
  });
  return outer;
}

function buildDetailPanel(){
  const panel=document.createElement("div");panel.className="detailPanel";
  const head=document.createElement("div");head.className="detailHead";
  const d=parseDate(state.selectedDate);
  const dd=document.createElement("div");dd.className="d";
  const _dw=d.getDay(),_isHol=isHoliday(state.selectedDate);
  const _dwColor=(_dw===0||_isHol)?"#d85a4a":_dw===6?"#2979ff":"var(--text)";
  const _dwName=["日","月","火","水","木","金","土"][_dw];
  dd.innerHTML=(d.getMonth()+1)+"月"+d.getDate()+"日（<span style='color:"+_dwColor+"'>"+_dwName+"</span>）";
  head.appendChild(dd);panel.appendChild(head);
  const list=document.createElement("div");list.className="detailList";
  const items=eventsForDate(state.selectedDate);
  if(!items.length){const e=document.createElement("div");e.className="emptyDetail";e.textContent="予定はありません";list.appendChild(e);}
  else items.forEach(ev=>list.appendChild(buildDetailItem(ev,state.selectedDate)));
  panel.appendChild(list);return panel;
}
function buildDetailItem(ev,occ){
  const row=document.createElement("div");row.className="detailItem";
  const col=colorOf(ev.colorId);
  const tb=document.createElement("div");tb.className="timeBlock";
  if(ev.time){
    const s=document.createElement("div");s.textContent=ev.time;tb.appendChild(s);
    if(ev.endTime){const e=document.createElement("div");e.textContent=ev.endTime;tb.appendChild(e);}
  }else{const a=document.createElement("div");a.textContent="終日";tb.appendChild(a);}
  row.appendChild(tb);
  const bar=document.createElement("div");bar.className="colorBar";bar.style.background=col.hex;row.appendChild(bar);
  if(ev.type==="task"){
    const cb=document.createElement("div");cb.className="checkbox"+(ev.done?" checked":"");
    cb.textContent=ev.done?"✓":"";
    cb.onclick=(e)=>{e.stopPropagation();toggleTaskDone(ev,occ);};row.appendChild(cb);
  }
  const txt=document.createElement("div");txt.className="txt";
  const ti=document.createElement("div");ti.className="ti"+(ev.done?" done":"");ti.textContent=ev.title;txt.appendChild(ti);
  if(ev.endDate&&ev.endDate>ev.date){const dr=document.createElement("div");dr.className="memoTxt";dr.textContent=ev.date+" 〜 "+ev.endDate;txt.appendChild(dr);}
  if(ev.memo){const m=document.createElement("div");m.className="memoTxt";m.textContent=ev.memo;txt.appendChild(m);}
  row.appendChild(txt);
  const del=document.createElement("button");del.className="delBtn";del.textContent="削除";
  del.onclick=(e)=>{e.stopPropagation();DATA.events=DATA.events.filter(x=>x.id!==ev.id);save();render();};
  row.appendChild(del);row.onclick=()=>openForm(ev);return row;
}
function toggleTaskDone(ev,occ){
  const orig=DATA.events.find(x=>x.id===ev.id);if(!orig)return;
  if(orig.repeat==="none")orig.done=!orig.done;
  else{orig.doneDates=orig.doneDates||[];const i=orig.doneDates.indexOf(occ);if(i>=0)orig.doneDates.splice(i,1);else orig.doneDates.push(occ);}
  save();render();
}

function buildTaskBody(){
  const wrap=document.createElement("div");wrap.className="taskWrap";
  const tasks=DATA.events.filter(e=>e.type==="task");
  if(!tasks.length){const e=document.createElement("div");e.className="emptyDetail";e.textContent="タスクはありません";wrap.appendChild(e);return wrap;}
  const byDate={};tasks.forEach(t=>{(byDate[t.date]=byDate[t.date]||[]).push(t);});
  Object.keys(byDate).sort().forEach(ds=>{
    const d=parseDate(ds);
    const h=document.createElement("div");h.className="taskDateHead";
    h.textContent=(d.getMonth()+1)+"月"+d.getDate()+"日（"+["日","月","火","水","木","金","土"][d.getDay()]+"）";
    wrap.appendChild(h);
    byDate[ds].forEach(t=>{
      const oc=t.repeat==="none"?t.date:todayStr;
      const dsp=Object.assign({},t);if(t.repeat!=="none")dsp.done=(t.doneDates||[]).includes(oc);
      wrap.appendChild(buildDetailItem(dsp,oc));
    });
  });return wrap;
}

function buildBottomNav(){
  const nav=document.createElement("div");nav.className="bottomnav";
  nav.append(
    mkNavBtn("▦","月",state.tab==="month",()=>{state.tab="month";render();}),
    mkNavBtn("☑","タスク",state.tab==="task",()=>{state.tab="task";render();}),
    mkNavBtn("▥","週",state.tab==="week",()=>{state.tab="week";render();}),
    mkNavBtn("⚙","設定",state.tab==="settings",()=>{state.tab="settings";render();})
  );
  const fab=document.createElement("button");fab.className="fab";fab.textContent="+";fab.onclick=()=>openForm(null);
  nav.appendChild(fab);return nav;
}
function mkNavBtn(icon,label,active,fn){
  const b=document.createElement("button");if(active)b.classList.add("active");
  const i=document.createElement("div");i.className="ic";i.textContent=icon;
  const t=document.createElement("div");t.textContent=label;
  b.append(i,t);b.onclick=fn;return b;
}

function buildSettingsHeader(){const h=document.createElement("div");h.className="header";const t=document.createElement("div");t.className="title";t.textContent="設定";h.appendChild(t);return h;}
function renderSettingsBody(wrap){wrap.innerHTML="";const fr=buildSettingsBody();while(fr.firstChild)wrap.appendChild(fr.firstChild);}
function buildSettingsBody(){
  const wrap=document.createElement("div");wrap.className="settingsWrap";
  const g1=document.createElement("div");g1.className="settingsGroup";
  const h1=document.createElement("h3");h1.textContent="月表示の切り替え方法";g1.appendChild(h1);
  [["vertical","縦スクロール","上下にスクロールして複数月を確認"],["horizontal","横スクロール","左右にスワイプして月を切り替え"]].forEach(([val,label,desc])=>{
    const opt=document.createElement("div");opt.className="settingsOpt";
    const left=document.createElement("div");
    const l=document.createElement("div");l.className="label";l.textContent=label;
    const d=document.createElement("div");d.className="desc";d.textContent=desc;
    left.append(l,d);
    const dot=document.createElement("div");dot.className="radioDot"+(DATA.monthScrollMode===val?" on":"");
    opt.append(left,dot);opt.onclick=()=>{DATA.monthScrollMode=val;save();render();};g1.appendChild(opt);
  });wrap.appendChild(g1);

  const g2=document.createElement("div");g2.className="settingsGroup";
  const colorTabBtn=document.createElement("div");colorTabBtn.style.cssText="display:flex;align-items:center;justify-content:space-between;background:#fff;border:0.5px solid var(--line);border-radius:12px;padding:13px 14px;cursor:pointer;";
  const colorTabLbl=document.createElement("div");colorTabLbl.style.fontSize="14px";colorTabLbl.textContent="色の管理";
  const colorTabArr=document.createElement("div");colorTabArr.style.cssText="font-size:12px;color:var(--sub);";colorTabArr.textContent="▼ タップで展開";
  colorTabBtn.append(colorTabLbl,colorTabArr);
  const colorGrid=document.createElement("div");colorGrid.style.cssText="display:none;flex-wrap:wrap;gap:8px;padding:12px;background:#fff;border:0.5px solid var(--line);border-radius:0 0 12px 12px;margin-top:-1px;";
  DATA.colors.forEach(c=>{
    const w2=document.createElement("div");w2.style.cssText="display:flex;flex-direction:column;align-items:center;gap:3px;cursor:pointer;";
    const sw=document.createElement("div");sw.style.cssText="width:36px;height:36px;border-radius:4px;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;color:#fff;position:relative;";
    sw.style.background=c.hex;if(c.name)sw.textContent=c.name[0];
    if(c.custom){const x=document.createElement("div");x.style.cssText="position:absolute;top:-4px;right:-4px;width:14px;height:14px;background:#ff5252;border-radius:50%;color:#fff;font-size:9px;font-weight:700;display:flex;align-items:center;justify-content:center;cursor:pointer;";x.textContent="×";x.onclick=(e)=>{e.stopPropagation();if(confirm("この色を削除しますか？")){DATA.colors=DATA.colors.filter(x=>x.id!==c.id);save();renderSettingsBody(wrap);}};sw.appendChild(x);}
    const lbl=document.createElement("div");lbl.style.cssText="font-size:9px;color:var(--sub);max-width:36px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;text-align:center;";lbl.textContent=c.name||"";
    w2.append(sw,lbl);w2.onclick=()=>renameColor(c,()=>renderSettingsBody(wrap));colorGrid.appendChild(w2);
  });
  let colorOpen=false;
  colorTabBtn.onclick=()=>{colorOpen=!colorOpen;colorGrid.style.display=colorOpen?"flex":"none";colorTabArr.textContent=colorOpen?"▲ 折りたたむ":"▼ タップで展開";};
  g2.append(colorTabBtn,colorGrid);wrap.appendChild(g2);

  const g3=document.createElement("div");g3.className="settingsGroup";
  const h3=document.createElement("h3");h3.textContent="カレンダー上の予定テキスト設定";g3.appendChild(h3);
  const fsOpt=document.createElement("div");fsOpt.className="settingsOpt";fsOpt.style.cssText="flex-direction:column;align-items:flex-start;gap:8px;";
  const fsLbl=document.createElement("div");fsLbl.className="label";fsLbl.textContent="文字の大きさ";
  const fsBtns=document.createElement("div");fsBtns.style.cssText="display:flex;gap:6px;width:100%;";
  ["極小","小","中","大","極大"].forEach((l,i)=>{
    const b=document.createElement("button");b.textContent=l;
    b.style.cssText="flex:1;padding:7px 0;border-radius:8px;border:1px solid var(--line);font-size:11px;cursor:pointer;";
    b.style.background=DATA.pillFontSize===(i+1)?"var(--accent)":"var(--btnbg)";b.style.color=DATA.pillFontSize===(i+1)?"#fff":"var(--sub)";
    b.onclick=()=>{DATA.pillFontSize=i+1;save();renderSettingsBody(wrap);};fsBtns.appendChild(b);
  });fsOpt.append(fsLbl,fsBtns);g3.appendChild(fsOpt);
  const fwOpt=document.createElement("div");fwOpt.className="settingsOpt";fwOpt.style.cssText="flex-direction:column;align-items:flex-start;gap:8px;";
  const fwLbl=document.createElement("div");fwLbl.className="label";fwLbl.textContent="文字の太さ";
  const fwBtns=document.createElement("div");fwBtns.style.cssText="display:flex;gap:6px;width:100%;";
  ["極細","細","中","太","極太"].forEach((l,i)=>{
    const b=document.createElement("button");b.textContent=l;
    b.style.cssText="flex:1;padding:7px 0;border-radius:8px;border:1px solid var(--line);font-size:11px;cursor:pointer;";
    b.style.background=DATA.pillFontWeight===(i+1)?"var(--accent)":"var(--btnbg)";b.style.color=DATA.pillFontWeight===(i+1)?"#fff":"var(--sub)";
    b.onclick=()=>{DATA.pillFontWeight=i+1;save();renderSettingsBody(wrap);};fwBtns.appendChild(b);
  });fwOpt.append(fwLbl,fwBtns);g3.appendChild(fwOpt);
  const tcOpt=document.createElement("div");tcOpt.className="settingsOpt";tcOpt.style.cssText="flex-direction:column;align-items:flex-start;gap:8px;";
  const tcLbl=document.createElement("div");tcLbl.className="label";tcLbl.textContent="文字の色";
  const tcBtns=document.createElement("div");tcBtns.style.cssText="display:flex;gap:8px;";
  [["black","黒"],["white","白"]].forEach(([val,lbl])=>{
    const b=document.createElement("button");b.style.cssText="padding:7px 20px;border-radius:8px;border:1px solid var(--line);font-size:13px;cursor:pointer;";b.textContent=lbl;
    b.style.background=DATA.pillTextColor===val?"var(--accent)":"var(--btnbg)";b.style.color=DATA.pillTextColor===val?"#fff":"var(--sub)";
    b.onclick=()=>{DATA.pillTextColor=val;save();renderSettingsBody(wrap);};tcBtns.appendChild(b);
  });tcOpt.append(tcLbl,tcBtns);g3.appendChild(tcOpt);
  wrap.appendChild(g3);return wrap;
}
function renameColor(c,cb){
  const nm=prompt("この色の名前を入力してください",c.name||"");
  if(nm!==null){c.name=nm.trim();save();if(cb)cb();}
}

function openForm(ev){
  state.editing=ev?Object.assign({},ev):{id:"e"+Date.now(),type:"event",title:"",date:state.selectedDate,endDate:"",time:"",endTime:"",colorId:DATA.colors[0].id,repeat:"none",memo:"",done:false};
  if(!state.editing.endTime)state.editing.endTime="";
  if(!state.editing.endDate)state.editing.endDate="";
  if(!state.editing._showAllColors)state.editing._showAllColors=false;
  const overlay=document.createElement("div");overlay.className="overlay";
  overlay.onclick=(e)=>{if(e.target===overlay)overlay.remove();};
  const sheet=document.createElement("div");sheet.className="sheet";
  overlay.appendChild(sheet);document.body.appendChild(overlay);renderForm(sheet,overlay);
}

function renderForm(sheet,overlay){
  const ed=state.editing;sheet.innerHTML="";
  const head=document.createElement("div");head.className="sheetHead";
  const cancel=document.createElement("button");cancel.className="cancel";cancel.textContent="キャンセル";cancel.onclick=()=>overlay.remove();
  const t=document.createElement("div");t.className="st";t.textContent=DATA.events.find(x=>x.id===ed.id)?"編集":"新規予定";
  const ok=document.createElement("button");ok.textContent="保存";
  ok.onclick=()=>{
    if(!ed.title.trim()){alert("タイトルを入力してください");return;}
    if(!DATA.history.includes(ed.title)){DATA.history.unshift(ed.title);DATA.history=DATA.history.slice(0,30);}
    trackColor(ed.colorId);
    const idx=DATA.events.findIndex(x=>x.id===ed.id);
    if(idx>=0)DATA.events[idx]=ed;else DATA.events.push(ed);
    save();overlay.remove();render();
  };
  head.append(cancel,t,ok);sheet.appendChild(head);
  const body=document.createElement("div");body.className="formBody";

  const tb=document.createElement("div");tb.className="typeBtns";
  ["event","task"].forEach(tp=>{
    const b=document.createElement("button");b.textContent=tp==="event"?"予定":"タスク";
    if(ed.type===tp)b.classList.add("active");b.onclick=()=>{ed.type=tp;renderForm(sheet,overlay);};tb.appendChild(b);
  });body.appendChild(tb);

  const titleRow=document.createElement("div");titleRow.className="formRow";
  const tl=document.createElement("label");tl.textContent="タイトル";
  const ti=document.createElement("input");ti.type="text";ti.value=ed.title;ti.placeholder="予定を入力";ti.oninput=()=>{ed.title=ti.value;};
  const hBtn=document.createElement("button");hBtn.className="smallIcon";hBtn.textContent="🕘";
  hBtn.onclick=()=>toggleSuggest(body,DATA.history,v=>{ed.title=v;ti.value=v;});
  const tBtn=document.createElement("button");tBtn.className="smallIcon";tBtn.textContent="★";
  tBtn.onclick=()=>openTemplatePicker(ed,sheet,overlay,ti);
  titleRow.append(tl,ti,hBtn,tBtn);body.appendChild(titleRow);

  const dateRow=document.createElement("div");dateRow.className="formRow";
  const dl=document.createElement("label");dl.textContent="日付";
  const dw=document.createElement("div");dw.style.cssText="flex:1;display:flex;align-items:center;gap:4px;";
  const di=document.createElement("input");di.type="date";di.value=ed.date;di.style.cssText="flex:1;border:none;background:none;font-size:13px;color:var(--text);outline:none;min-width:0;";di.oninput=()=>{ed.date=di.value;};
  const dsep=document.createElement("div");dsep.textContent="〜";dsep.style.cssText="color:var(--sub);font-size:12px;flex-shrink:0;";
  const di2=document.createElement("input");di2.type="date";di2.value=ed.endDate||"";di2.style.cssText="flex:1;border:none;background:none;font-size:13px;color:var(--sub);outline:none;min-width:0;";di2.oninput=()=>{ed.endDate=di2.value;};
  dw.append(di,dsep,di2);dateRow.append(dl,dw);body.appendChild(dateRow);

  const timeRow=document.createElement("div");timeRow.className="formRow";
  const tml=document.createElement("label");tml.textContent="時間";
  const tw=document.createElement("div");tw.style.cssText="flex:1;display:flex;align-items:center;gap:6px;";
  const sp=document.createElement("div");sp.className="timePill";sp.textContent=ed.time||"開始";sp.style.color=ed.time?"var(--text)":"var(--sub)";
  sp.onclick=()=>openCalcKeypad(ed.time,v=>{ed.time=v;renderForm(sheet,overlay);});
  const tmsep=document.createElement("div");tmsep.className="timeSep";tmsep.textContent="〜";
  const ep=document.createElement("div");ep.className="timePill";ep.textContent=ed.endTime||"終了";ep.style.color=ed.endTime?"var(--text)":"var(--sub)";
  ep.onclick=()=>openCalcKeypad(ed.endTime,v=>{ed.endTime=v;renderForm(sheet,overlay);});
  tw.append(sp,tmsep,ep);timeRow.append(tml,tw);
  if(ed.time||ed.endTime){const clr=document.createElement("button");clr.className="smallIcon";clr.textContent="×";clr.onclick=()=>{ed.time="";ed.endTime="";renderForm(sheet,overlay);};timeRow.appendChild(clr);}
  body.appendChild(timeRow);

  /* 色ピッカー: 使用順上位8色 + 展開 */
  const colorRow=document.createElement("div");colorRow.className="formRow";colorRow.style.alignItems="flex-start";
  const cl=document.createElement("label");cl.textContent="色";cl.style.paddingTop="10px";
  const cw=document.createElement("div");cw.style.flex="1";
  const hint=document.createElement("div");hint.className="colorHint";hint.textContent="長押しで名前を登録できます";
  const cp=document.createElement("div");cp.className="colorPick";
  // 使用順で並べた色、最初は8色
  const orderedColors=sortedColors();
  const visibleColors=ed._showAllColors?orderedColors:orderedColors.slice(0,8);
  function makeSwatch(c2){
    const sw=document.createElement("div");sw.className="swatch"+(ed.colorId===c2.id?" sel":"");
    sw.style.background=c2.hex;
    if(c2.name){sw.textContent=c2.name[0];sw.style.textShadow="0 1px 2px rgba(0,0,0,.35)";}
    let timer=null,lp=false;
    const sp2=()=>{lp=false;timer=setTimeout(()=>{lp=true;const nm=prompt("この色の名前を入力してください",c2.name||"");if(nm!==null){c2.name=nm.trim();save();renderForm(sheet,overlay);}},600);};
    const ep2=()=>clearTimeout(timer);
    sw.addEventListener("touchstart",sp2);sw.addEventListener("touchend",ep2);
    sw.addEventListener("mousedown",sp2);sw.addEventListener("mouseup",ep2);
    sw.addEventListener("click",()=>{if(lp)return;ed.colorId=c2.id;renderForm(sheet,overlay);});
    return sw;
  }
  visibleColors.forEach(c2=>cp.appendChild(makeSwatch(c2)));
  // ＋色作成ボタン
  const moreBtn=document.createElement("button");
  moreBtn.style.cssText="font-size:11px;background:var(--btnbg);border:1px solid var(--line);border-radius:12px;padding:3px 8px;cursor:pointer;color:var(--accent);white-space:nowrap;align-self:center;";
  moreBtn.textContent=ed._showAllColors?"折りたたむ":"＋色作成";
  moreBtn.onclick=()=>{
    if(!ed._showAllColors){ed._showAllColors=true;renderForm(sheet,overlay);}
    else{openCustomColorPicker(sheet,overlay);}
  };
  cp.appendChild(moreBtn);
  cw.append(hint,cp);colorRow.append(cl,cw);body.appendChild(colorRow);

  const repRow=document.createElement("div");repRow.className="formRow";
  const rl=document.createElement("label");rl.textContent="繰り返し";
  const rs=document.createElement("select");
  [["none","なし"],["daily","毎日"],["weekly","毎週"],["monthly","毎月"],["yearly","毎年"]].forEach(([v,l])=>{
    const o=document.createElement("option");o.value=v;o.textContent=l;if(ed.repeat===v)o.selected=true;rs.appendChild(o);
  });rs.onchange=()=>{ed.repeat=rs.value;};repRow.append(rl,rs);body.appendChild(repRow);

  const memoRow=document.createElement("div");memoRow.className="formRow";
  const ml=document.createElement("label");ml.textContent="メモ";
  const mt=document.createElement("textarea");mt.value=ed.memo||"";mt.placeholder="メモを入力";mt.oninput=()=>{ed.memo=mt.value;};
  memoRow.append(ml,mt);body.appendChild(memoRow);sheet.appendChild(body);
}

function openCustomColorPicker(sheet,overlay){
  const ov2=document.createElement("div");ov2.className="overlay";ov2.style.zIndex=70;
  ov2.onclick=(e)=>{if(e.target===ov2)ov2.remove();};
  const sh2=document.createElement("div");sh2.className="sheet";
  const head=document.createElement("div");head.className="sheetHead";
  const close=document.createElement("button");close.className="cancel";close.textContent="閉じる";close.onclick=()=>ov2.remove();
  const tt=document.createElement("div");tt.className="st";tt.textContent="カラーチャート";
  head.append(close,tt,document.createElement("span"));sh2.appendChild(head);

  const body=document.createElement("div");body.style.padding="16px";
  // Color picker using HTML5 color input
  const previewRow=document.createElement("div");previewRow.style.cssText="display:flex;align-items:center;gap:12px;margin-bottom:16px;";
  const preview=document.createElement("div");preview.className="colorPreview";
  let currentHex="#FF6B6B";preview.style.background=currentHex;
  const hexLabel=document.createElement("div");hexLabel.style.cssText="font-size:13px;color:var(--sub);font-weight:600;";hexLabel.textContent=currentHex.toUpperCase();
  previewRow.append(preview,hexLabel);body.appendChild(previewRow);

  // HSL sliders
  let hue=0,sat=100,lig=60;
  function hslToHex(h,s,l){
    const a=s*Math.min(l,100-l)/100;const f=n=>{const k=(n+h/30)%12;const color=l-a*Math.max(Math.min(k-3,9-k,1),-1);return Math.round(255*color/100).toString(16).padStart(2,'0');};
    return "#"+f(0)+f(8)+f(4);
  }
  function updatePreview(){currentHex=hslToHex(hue,sat,lig);preview.style.background=currentHex;hexLabel.textContent=currentHex.toUpperCase();}

  const hueRow=document.createElement("div");hueRow.style.marginBottom="12px";
  const hueLbl=document.createElement("div");hueLbl.style.cssText="font-size:12px;color:var(--sub);margin-bottom:4px;";hueLbl.textContent="色相";
  const hueInput=document.createElement("input");hueInput.type="range";hueInput.min=0;hueInput.max=360;hueInput.value=hue;
  hueInput.style.cssText="width:100%;height:16px;border-radius:8px;cursor:pointer;-webkit-appearance:none;appearance:none;background:linear-gradient(to right,hsl(0,100%,60%),hsl(30,100%,60%),hsl(60,100%,60%),hsl(90,100%,60%),hsl(120,100%,60%),hsl(150,100%,60%),hsl(180,100%,60%),hsl(210,100%,60%),hsl(240,100%,60%),hsl(270,100%,60%),hsl(300,100%,60%),hsl(330,100%,60%),hsl(360,100%,60%));";
  hueInput.oninput=()=>{hue=parseInt(hueInput.value);updatePreview();};
  hueRow.append(hueLbl,hueInput);body.appendChild(hueRow);

  const satRow=document.createElement("div");satRow.style.marginBottom="12px";
  const satLbl=document.createElement("div");satLbl.style.cssText="font-size:12px;color:var(--sub);margin-bottom:4px;";satLbl.textContent="彩度";
  const satInput=document.createElement("input");satInput.type="range";satInput.min=0;satInput.max=100;satInput.value=sat;
  satInput.style.cssText="width:100%;height:16px;border-radius:8px;cursor:pointer;-webkit-appearance:none;appearance:none;";
  satInput.oninput=()=>{sat=parseInt(satInput.value);updatePreview();};
  satRow.append(satLbl,satInput);body.appendChild(satRow);

  const ligRow=document.createElement("div");ligRow.style.marginBottom="12px";
  const ligLbl=document.createElement("div");ligLbl.style.cssText="font-size:12px;color:var(--sub);margin-bottom:4px;";ligLbl.textContent="明度";
  const ligInput=document.createElement("input");ligInput.type="range";ligInput.min=10;ligInput.max=90;ligInput.value=lig;
  ligInput.style.cssText="width:100%;height:16px;border-radius:8px;cursor:pointer;-webkit-appearance:none;appearance:none;";
  ligInput.oninput=()=>{lig=parseInt(ligInput.value);updatePreview();};
  ligRow.append(ligLbl,ligInput);body.appendChild(ligRow);

  // プリセット色
  const presetRow=document.createElement("div");presetRow.style.cssText="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:16px;";
  const presetLbl=document.createElement("div");presetLbl.style.cssText="width:100%;font-size:12px;color:var(--sub);margin-bottom:4px;";presetLbl.textContent="プリセット";
  presetRow.appendChild(presetLbl);
  ["#FF6B6B","#FF8E53","#FFC300","#2ECC71","#1ABC9C","#3498DB","#9B59B6","#E91E63","#607D8B","#795548"].forEach(hex=>{
    const sw=document.createElement("div");sw.style.cssText="width:32px;height:32px;border-radius:6px;cursor:pointer;background:"+hex+";border:2px solid transparent;";
    sw.onclick=()=>{currentHex=hex;preview.style.background=hex;hexLabel.textContent=hex.toUpperCase();
      // Update sliders from hex
      const r=parseInt(hex.slice(1,3),16)/255,g=parseInt(hex.slice(3,5),16)/255,b=parseInt(hex.slice(5,7),16)/255;
      const max=Math.max(r,g,b),min=Math.min(r,g,b);
      lig=Math.round((max+min)/2*100);
      sat=max===min?0:Math.round((max-min)/(lig>50?2-max-min:max+min)*100);
      hue=max===min?0:max===r?Math.round((g-b)/(max-min)*60):max===g?Math.round(((b-r)/(max-min)+2)*60):Math.round(((r-g)/(max-min)+4)*60);
      if(hue<0)hue+=360;
      hueInput.value=hue;satInput.value=sat;ligInput.value=lig;
    };
    presetRow.appendChild(sw);
  });
  body.appendChild(presetRow);

  const addBtn=document.createElement("button");addBtn.style.cssText="width:100%;padding:13px;border-radius:12px;border:none;background:var(--accent);color:#fff;font-size:15px;font-weight:600;cursor:pointer;";
  addBtn.textContent="この色をパレットに追加";
  addBtn.onclick=()=>{
    const newColor={id:"custom_"+Date.now(),hex:currentHex,name:"",custom:true};
    DATA.colors.push(newColor);save();
    state.editing.colorId=newColor.id;state.editing._showAllColors=true;
    ov2.remove();renderForm(sheet,overlay);
  };
  body.appendChild(addBtn);
  sh2.appendChild(body);ov2.appendChild(sh2);document.body.appendChild(ov2);
}

function toggleSuggest(body,list,onPick){
  const ex=body.querySelector(".suggestBox");if(ex){ex.remove();return;}
  const box=document.createElement("div");box.className="suggestBox";
  if(!list.length){box.textContent="履歴はありません";box.style.cssText="color:var(--sub);font-size:12px;";}
  list.slice(0,12).forEach(v=>{const chip=document.createElement("div");chip.className="suggestChip";chip.textContent=v;chip.onclick=()=>{onPick(v);box.remove();};box.appendChild(chip);});
  body.insertBefore(box,body.children[1]);
}
function openTemplatePicker(ed,sheet,overlay,ti){
  const ov=document.createElement("div");ov.className="overlay";ov.style.zIndex=70;
  ov.onclick=(e)=>{if(e.target===ov)ov.remove();};
  const sh=document.createElement("div");sh.className="sheet";
  const head=document.createElement("div");head.className="sheetHead";
  const close=document.createElement("button");close.className="cancel";close.textContent="閉じる";close.onclick=()=>ov.remove();
  const tt=document.createElement("div");tt.className="st";tt.textContent="テンプレート";
  const add=document.createElement("button");add.textContent="現在の内容を追加";add.style.fontSize="12px";
  add.onclick=()=>{DATA.templates.push({id:"t"+Date.now(),title:ed.title||"無題",time:ed.time,endTime:ed.endTime||"",colorId:ed.colorId,memo:ed.memo});save();ov.remove();openTemplatePicker(ed,sheet,overlay,ti);};
  head.append(close,tt,add);sh.appendChild(head);
  const body=document.createElement("div");body.className="formBody";
  if(!DATA.templates.length){const e=document.createElement("div");e.className="emptyDetail";e.textContent="テンプレートはありません";body.appendChild(e);}
  DATA.templates.forEach(tp=>{
    const row=document.createElement("div");row.className="detailItem";
    const dot=document.createElement("div");dot.className="colorBar";dot.style.background=colorOf(tp.colorId).hex;
    const txt=document.createElement("div");txt.className="txt";
    txt.innerHTML='<div class="ti">'+tp.title+'</div>'+(tp.time?'<div class="memoTxt">'+tp.time+(tp.endTime?"〜"+tp.endTime:"")+'</div>':"");
    const del=document.createElement("button");del.className="delBtn";del.textContent="削除";
    del.onclick=(e)=>{e.stopPropagation();DATA.templates=DATA.templates.filter(x=>x.id!==tp.id);save();ov.remove();openTemplatePicker(ed,sheet,overlay,ti);};
    row.append(dot,txt,del);
    row.onclick=()=>{ed.title=tp.title;ed.time=tp.time;ed.endTime=tp.endTime||"";ed.colorId=tp.colorId;ed.memo=tp.memo;ov.remove();renderForm(sheet,overlay);};
    body.appendChild(row);
  });
  sh.appendChild(body);ov.appendChild(sh);document.body.appendChild(ov);
}

function openCalcKeypad(initial,onConfirm){
  let digits=(initial||"").replace(":","");
  const ov=document.createElement("div");ov.className="calcOverlay";ov.onclick=(e)=>{if(e.target===ov)ov.remove();};
  const sh=document.createElement("div");sh.className="calcSheet";
  const disp=document.createElement("div");disp.className="calcDisplay";
  const fmt=()=>{if(!digits.length)return"--:--";const d=digits.padStart(4,"0").slice(-4);return d.slice(0,2)+":"+d.slice(2,4);};
  disp.textContent=fmt();sh.appendChild(disp);
  const grid=document.createElement("div");grid.className="calcGrid";
  ["1","2","3","4","5","6","7","8","9","00","0","⌫"].forEach(k=>{
    const b=document.createElement("button");b.textContent=k;
    b.onclick=()=>{if(k==="⌫")digits=digits.slice(0,-1);else digits=(digits+k).slice(-4);disp.textContent=fmt();};grid.appendChild(b);
  });sh.appendChild(grid);
  const br=document.createElement("div");br.className="calcBottomRow";
  const cb=document.createElement("button");cb.className="cancel";cb.textContent="キャンセル";cb.onclick=()=>ov.remove();
  const okb=document.createElement("button");okb.className="ok";okb.textContent="確定";
  okb.onclick=()=>{
    if(!digits.length){onConfirm("");ov.remove();return;}
    const d=digits.padStart(4,"0").slice(-4);
    const hh=Math.min(23,parseInt(d.slice(0,2),10)),mm=Math.min(59,parseInt(d.slice(2,4),10));
    onConfirm(String(hh).padStart(2,"0")+":"+String(mm).padStart(2,"0"));ov.remove();
  };
  br.append(cb,okb);sh.appendChild(br);ov.appendChild(sh);document.body.appendChild(ov);
}

render();
"""
with open("/tmp/new_js.txt", "w") as f:
    f.write(js)
print("JS written:", len(js), "chars")
