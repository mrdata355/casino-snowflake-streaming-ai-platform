(() => {
  const $ = id => document.getElementById(id);
  const safe = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const toast = text => {
    let node=document.querySelector('.manager-action-toast'); if(node) node.remove();
    node=document.createElement('div'); node.className='lab-score-toast manager-action-toast';
    node.innerHTML=`<strong>OpsReady</strong><div style="margin-top:4px">${safe(text)}</div>`;
    document.body.appendChild(node); setTimeout(()=>node.remove(),3500);
  };
  function json(key, fallback){try{return JSON.parse(localStorage.getItem(key)||JSON.stringify(fallback))}catch(_){return fallback}}
  function read(){
    const labs=json('opsreadyLabEvidence',[]), state=json('opsreadyState',{}), live=json('opsreadyV6LiveEvidence',[]), assignments=json('opsreadyAssignments',[]);
    return {labs, grades:state.gradeHistory||[], live, assignments};
  }
  function allEvidence(){
    const {labs,grades,live}=read();
    return [
      ...labs.map(x=>({name:x.lab||'Interactive Lab',score:Number(x.score)||0,detail:x.detail||'',at:x.at,type:'Lab'})),
      ...grades.map(x=>({name:x.name||'Graded Drill',score:Number(x.score)||0,detail:'Rubric graded',at:x.at,type:'Drill'})),
      ...live.map(x=>({name:`${x.platform||'Platform'} ${x.taskId||'live task'}`,score:x.success?100:0,detail:x.success?`Real sandbox ${x.namespace||''}`:`Live failure: ${x.error||''}`,at:x.at,type:'Real Sandbox'})),
    ].sort((a,b)=>new Date(b.at||0)-new Date(a.at||0));
  }
  function assignments(){return json('opsreadyAssignments',[])}
  function saveAssignments(rows){localStorage.setItem('opsreadyAssignments',JSON.stringify(rows.slice(-100)))}
  function assign(target, drill='Snowflake Cost + Query Pathology'){
    const rows=assignments(); rows.push({target,drill,status:'Assigned',at:new Date().toISOString()}); saveAssignments(rows); render(); toast(`${drill} assigned to ${target}.`)
  }
  function exportEvidence(){
    const rows=allEvidence();
    const csv=['Type,Attempt,Score,Evidence,When',...rows.map(x=>[x.type,x.name,x.score,x.detail,x.at].map(v=>`"${String(v??'').replace(/"/g,'""')}"`).join(','))].join('\n');
    const blob=new Blob([csv],{type:'text/csv;charset=utf-8'}),url=URL.createObjectURL(blob),a=document.createElement('a');
    a.href=url;a.download=`opsready-evidence-${new Date().toISOString().slice(0,10)}.csv`;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),500);toast('Evidence CSV exported.');
  }
  function clearEvidence(){
    if(!confirm('Clear browser-only OpsReady evidence and assignments?'))return;
    ['opsreadyLabEvidence','opsreadyV6LiveEvidence','opsreadyAssignments'].forEach(k=>localStorage.removeItem(k));
    const state=json('opsreadyState',{});state.gradeHistory=[];localStorage.setItem('opsreadyState',JSON.stringify(state));render();toast('Browser evidence cleared.');
  }
  function markKnownControls(){
    const selectors=['#roleToggle','.nav-item','.jump-btn','#gradeWeekly','#gradeMonthly','#gradeFinops','#generateTraining','.control-launch','#openControlFull','#captureLabScore','#closeSim','#simulatorCards button'];
    selectors.forEach(sel=>document.querySelectorAll(sel).forEach(b=>b.dataset.wired='true'));
  }
  async function uiSelfTest(){
    markKnownControls(); const issues=[];
    const seen=new Set();document.querySelectorAll('[id]').forEach(el=>{if(seen.has(el.id))issues.push(`Duplicate id: ${el.id}`);seen.add(el.id)});
    document.querySelectorAll('.nav-item[data-view]').forEach(b=>{if(!document.getElementById(b.dataset.view))issues.push(`Missing nav target: ${b.dataset.view}`)});
    document.querySelectorAll('.jump-btn[data-jump]').forEach(b=>{if(!document.getElementById(b.dataset.jump))issues.push(`Missing jump target: ${b.dataset.jump}`)});
    ['roleToggle','gradeWeekly','gradeMonthly','gradeFinops','generateTraining','openControlFull','captureLabScore','closeSim'].forEach(id=>{const el=$(id);if(!el)issues.push(`Missing control: ${id}`)});
    const cards=document.querySelectorAll('#simulatorCards .sim-card');if(!cards.length)issues.push('Simulation Library has no rendered cards.');
    const frame=$('controlFrame');if(!frame||!frame.getAttribute('src'))issues.push('Production Control Room iframe has no source.');
    const visibleButtons=[...document.querySelectorAll('button')].filter(b=>b.offsetParent!==null);
    const knownUnmarked=visibleButtons.filter(b=>!b.dataset.wired && !b.closest('#sopList') && !b.onclick && !b.classList.contains('assign-person'));
    if(knownUnmarked.length) issues.push(`${knownUnmarked.length} visible button(s) are not registered with the UI integrity layer.`);
    let assetResults=[];
    for(const path of ['/simulators/v4-reasoning-agentops.html','/simulators/v5-business-project-quest.html','/simulators/v6-full-job-cycle-lab.html','/simulators/neon-harbor-production.html']){
      try{const r=await fetch(path,{cache:'no-store'});assetResults.push(`${path}: ${r.ok?'OK':'HTTP '+r.status}`);if(!r.ok)issues.push(`Asset unavailable: ${path}`)}catch(e){issues.push(`Asset fetch failed: ${path}`)}
    }
    const result=$('uiSelfTestResult');if(result){result.className=`feedback ${issues.length?'partial':'pass'}`;result.innerHTML=`<strong>${issues.length?'UI audit found '+issues.length+' item(s)':'UI audit passed'}</strong><p>${issues.length?safe(issues.join(' • ')):'Navigation targets, primary actions, simulator assets and visible controls passed the browser self-test.'}</p><small>${safe(assetResults.join(' | '))}</small>`}
    toast(issues.length?`UI self-test found ${issues.length} item(s).`:'UI self-test passed.');
  }
  function certification(){
    const all=allEvidence(),avg=all.length?Math.round(all.reduce((a,b)=>a+b.score,0)/all.length):0,real=all.filter(x=>x.type==='Real Sandbox'&&x.score===100).length;
    const cards=document.querySelectorAll('#certification .cert-card');
    if(cards[2]){const s=cards[2].querySelector('strong');const achieved=avg>=90&&all.length>=5;if(s)s.textContent=achieved?'Achieved':`${avg}% / 90%`;cards[2].classList.toggle('achieved',achieved);cards[2].classList.toggle('current',!achieved)}
    if(cards[3]){const s=cards[3].querySelector('strong');const achieved=avg>=93&&all.length>=15&&real>=3;if(s)s.textContent=achieved?'Achieved':`Requires 93% + 15 attempts + 3 live`;cards[3].classList.toggle('achieved',achieved)}
    const out=$('certCalcResult');if(out)out.innerHTML=`<strong>${avg||0}% evidence average</strong><p>${all.length} graded attempts • ${real} successful real-sandbox tasks.</p>`;
    toast('Certification evidence recalculated.');
  }
  function injectCertification(){
    const host=$('certification');if(!host||$('certActionPanel'))return;
    const panel=document.createElement('article');panel.id='certActionPanel';panel.className='panel';panel.innerHTML=`<div class="panel-head"><h2>Certification actions</h2><span class="pill">Evidence based</span></div><div style="display:flex;gap:8px;flex-wrap:wrap"><button id="recalcCert" class="btn btn-primary">Recalculate From Evidence</button><button id="showCertReq" class="btn">Show Requirements</button></div><div id="certCalcResult" class="callout" style="margin-top:10px">Run the calculation after completing drills and live sandbox tasks.</div><div id="certReq" class="generated hidden" style="margin-top:10px"><strong>Senior Resilience:</strong> ≥90% evidence average with at least 5 attempts.<br><strong>Staff / Principal:</strong> ≥93%, at least 15 attempts, and at least 3 successful real-sandbox tasks. These are OpsReady demo thresholds, not an external certification.</div>`;host.appendChild(panel);
    $('recalcCert').dataset.wired='true';$('showCertReq').dataset.wired='true';$('recalcCert').onclick=certification;$('showCertReq').onclick=()=>$('certReq').classList.toggle('hidden');
  }
  function injectTeamActions(){
    const table=document.querySelector('#manager table');if(!table||table.dataset.actionsAdded)return;table.dataset.actionsAdded='true';
    const hr=table.querySelector('thead tr');if(hr)hr.insertAdjacentHTML('beforeend','<th>Action</th>');
    table.querySelectorAll('tbody tr').forEach(row=>{const name=row.cells[0]?.textContent?.trim()||'Engineer';const td=document.createElement('td'),b=document.createElement('button');b.className='btn assign-person';b.textContent='Assign';b.dataset.wired='true';b.onclick=()=>assign(name);td.appendChild(b);row.appendChild(td)});
    const panels=[...document.querySelectorAll('#manager .panel')];const rec=panels.find(p=>p.textContent.includes('Recommended next team drill'));if(rec&&!rec.querySelector('.assign-team')){const b=document.createElement('button');b.className='btn btn-primary assign-team';b.textContent='Assign Drill to Team';b.dataset.wired='true';b.onclick=()=>assign('Data Engineering Team');rec.appendChild(b)}
  }
  function render(){
    const host=$('manager');if(!host)return;injectTeamActions();
    let panel=$('managerEvidencePanel');if(!panel){panel=document.createElement('article');panel.id='managerEvidencePanel';panel.className='panel';host.insertBefore(panel,host.children[2]||null)}
    const all=allEvidence(),as=assignments(),avg=all.length?Math.round(all.reduce((a,b)=>a+b.score,0)/all.length):0,last=all[0];const labs=json('opsreadyLabEvidence',[]),unsafe=labs.reduce((sum,x)=>{const m=String(x.detail||'').match(/unsafe\s+(\d+)/i);return sum+(m?Number(m[1]):0)},0);
    panel.innerHTML=`<div class="panel-head"><h2>Captured Production Evidence</h2><span class="pill">Live browser evidence</span></div><div class="metric-grid compact"><article class="metric-card"><span>Recorded attempts</span><strong>${all.length}</strong><small>Labs + drills + live</small></article><article class="metric-card"><span>Average score</span><strong>${avg||'—'}${avg?'%':''}</strong><small>Recorded evidence</small></article><article class="metric-card"><span>Latest score</span><strong>${last?last.score+'%':'—'}</strong><small>${last?safe(last.name):'No attempt yet'}</small></article><article class="metric-card"><span>Assignments</span><strong>${as.length}</strong><small>${unsafe} unsafe action penalties</small></article></div><div class="table-wrap"><table><thead><tr><th>Type</th><th>Attempt</th><th>Score</th><th>Evidence</th><th>When</th></tr></thead><tbody>${all.slice(0,10).map(x=>`<tr><td>${safe(x.type)}</td><td>${safe(x.name)}</td><td>${x.score}%</td><td>${safe(x.detail)}</td><td>${x.at?new Date(x.at).toLocaleString():'—'}</td></tr>`).join('')||'<tr><td colspan="5">Complete a graded drill or live task to populate this table.</td></tr>'}</tbody></table></div>`;
    let actions=$('managerActionPanel');if(!actions){actions=document.createElement('article');actions.id='managerActionPanel';actions.className='panel';host.appendChild(actions)}
    actions.innerHTML=`<div class="panel-head"><h2>Manager actions</h2><span class="pill">Functional controls</span></div><div style="display:flex;gap:8px;flex-wrap:wrap"><button id="assignTeamDrill" class="btn btn-primary">Assign Recommended Drill</button><button id="refreshManager" class="btn">Refresh Evidence</button><button id="exportEvidence" class="btn">Export Evidence CSV</button><button id="runUiSelfTest" class="btn">Run UI Self-Test</button><button id="clearEvidence" class="btn btn-ghost">Clear Browser Evidence</button></div><div id="uiSelfTestResult" class="callout" style="margin-top:10px">Run UI Self-Test to verify navigation, primary buttons, duplicate IDs and simulator assets.</div>`;
    ['assignTeamDrill','refreshManager','exportEvidence','runUiSelfTest','clearEvidence'].forEach(id=>$(id).dataset.wired='true');
    $('assignTeamDrill').onclick=()=>assign('Data Engineering Team');$('refreshManager').onclick=()=>{render();toast('Manager evidence refreshed.')};$('exportEvidence').onclick=exportEvidence;$('runUiSelfTest').onclick=uiSelfTest;$('clearEvidence').onclick=clearEvidence;
    markKnownControls();
  }
  window.addEventListener('storage',render);
  window.addEventListener('message',e=>{if(!e.data||e.data.type!=='opsready-lab-score')return;let arr=json('opsreadyLabEvidence',[]);arr.push({lab:e.data.lab||'Production Lab',score:Math.round(Number(e.data.score)||0),detail:e.data.detail||'',at:new Date().toISOString()});localStorage.setItem('opsreadyLabEvidence',JSON.stringify(arr.slice(-50)));setTimeout(render,50)});
  document.addEventListener('click',e=>{if(e.target?.dataset?.view==='manager')setTimeout(render,50);if(e.target?.dataset?.view==='certification')setTimeout(injectCertification,50)});
  injectCertification();render();
})();