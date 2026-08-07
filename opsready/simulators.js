(() => {
  const $ = id => document.getElementById(id);
  const labs = [
    ['Neon Harbor Production Control Room','Live pipeline topology, Kafka partitions, Databricks notebook execution, Snowflake query profile, join lab, reconciliation gate, CI/CD rollback, incident consequences and handoff scoring.','/simulators/neon-harbor-production.html','Production','featured'],
    ['V4 Architecture + Jinja + AgentOps','Staff/principal decision reasoning, 15 Jinja coding labs, the 9-agent/6-model swarm, 12 governed agent incidents, and a searchable 127-agent architecture library.','/simulators/v4-reasoning-agentops.html','V4 Reasoning','featured'],
    ['Broken Pipeline: 30 Defects','Full end-to-end repair library across Source, Kafka, Databricks, Delta, Snowflake, dbt, Serving, FinOps, CI/CD, Recovery, Security, Observability, ML and Agents.','/simulators/broken-pipeline-30.html','30 Defects','featured'],
    ['Daily Operations SOP','Ordered production health, quality, deployment, verification, recovery, and handoff workflow.','/simulators/daily-operations.html','Daily','']
  ];
  const coreCount=document.querySelector('.control-metrics .metric-card:nth-child(2) strong');if(coreCount)coreCount.textContent='30 + V4';
  const coreSub=document.querySelector('.control-metrics .metric-card:nth-child(2) small');if(coreSub)coreSub.textContent='defects + architecture/Jinja/AgentOps';
  const repairBtn=document.querySelectorAll('.control-launch')[1];if(repairBtn){repairBtn.textContent='30-Defect Repair Bay';repairBtn.dataset.title='30-Defect Broken Pipeline Repair Bay'}
  const toolbar=document.querySelector('.control-toolbar');
  if(toolbar && !toolbar.querySelector('[data-v4-reasoning]')){
    const b=document.createElement('button');b.className='btn control-launch';b.dataset.src='/simulators/v4-reasoning-agentops.html';b.dataset.title='V4 Architecture + Jinja + AgentOps';b.dataset.v4Reasoning='1';b.textContent='V4 Reasoning + AgentOps';
    const full=$('openControlFull');toolbar.insertBefore(b,full||null);
  }
  function showToast(text){let old=document.querySelector('.lab-score-toast');if(old)old.remove();let d=document.createElement('div');d.className='lab-score-toast';d.innerHTML='<strong>OpsReady evidence captured</strong><div style="margin-top:4px">'+text+'</div>';document.body.appendChild(d);setTimeout(()=>d.remove(),4200)}
  function openModal(title,url){if(!$('simModal'))return;$('simTitle').textContent=title;$('simFrame').src=url;$('simModal').classList.remove('hidden')}
  if($('closeSim'))$('closeSim').onclick=()=>{$('simModal').classList.add('hidden');$('simFrame').src='about:blank'};
  function renderLibrary(){let host=$('simulatorCards');if(!host)return;host.innerHTML='';labs.forEach(([title,desc,url,badge,cls])=>{let c=document.createElement('article');c.className='sim-card '+cls;c.innerHTML=`<div class="lab-meta"><span class="pill">${badge}</span><span class="pill">Interactive</span></div><h3>${title}</h3><p class="muted">${desc}</p><button class="btn btn-primary">Launch Full Lab</button>`;c.querySelector('button').onclick=()=>openModal(title,url);host.appendChild(c)})}
  let controlUrl='/simulators/neon-harbor-production.html',controlTitle='Neon Harbor Production Control Room';
  document.querySelectorAll('.control-launch').forEach(b=>b.onclick=()=>{document.querySelectorAll('.control-launch').forEach(x=>x.classList.remove('active'));b.classList.add('active');controlUrl=b.dataset.src;controlTitle=b.dataset.title;$('controlFrame').src=controlUrl;$('controlTitle').textContent=controlTitle});
  if($('openControlFull'))$('openControlFull').onclick=()=>openModal(controlTitle,controlUrl);
  function storeEvidence(lab,score,detail){let hist=[];try{hist=JSON.parse(localStorage.getItem('opsreadyLabEvidence')||'[]')}catch(e){}hist.push({lab,score,detail,at:new Date().toISOString()});localStorage.setItem('opsreadyLabEvidence',JSON.stringify(hist.slice(-50)))}
  function capture(){let f=$('controlFrame');if(!f)return;try{let doc=f.contentDocument,score=null,detail='';let actionScore=doc.getElementById('score'), actionMatch=actionScore&&actionScore.textContent.match(/(\d+)\s*\/\s*120/);let v4=doc.getElementById('masterScore'),v4Match=v4&&v4.textContent.match(/(\d+)%/);if(actionMatch){score=Math.round(Number(actionMatch[1])/120*100);let card=doc.getElementById('scorecard');let unsafe=card&&card.textContent.match(/Unsafe actions:\s*(\d+)/i);detail='action score '+actionMatch[1]+'/120; unsafe '+(unsafe?unsafe[1]:'0')}else if(v4Match){score=Number(v4Match[1]);let sub=doc.getElementById('masterSub');detail='V4 reasoning mastery; '+(sub?sub.textContent:'architecture + Jinja + AgentOps')}else{score=0;detail='No graded action score found yet'}if($('labScore'))$('labScore').textContent=score+'%';if($('labScoreSub'))$('labScoreSub').textContent=detail;storeEvidence(controlTitle,score,detail);showToast(`${controlTitle}: ${score}% — ${detail}`)}catch(e){showToast('Complete/grade the lab first, then capture the score again.')}}
  if($('captureLabScore'))$('captureLabScore').onclick=capture;
  window.addEventListener('message',e=>{if(!e.data||e.data.type!=='opsready-lab-score')return;let score=Math.round(Number(e.data.score)||0),detail=e.data.detail||e.data.lab||'Interactive lab';if($('labScore'))$('labScore').textContent=score+'%';if($('labScoreSub'))$('labScoreSub').textContent=detail;storeEvidence(e.data.lab||'Production Lab',score,detail);showToast(`${e.data.lab||'Lab'}: ${score}%`)});
  renderLibrary();
  if(!document.querySelector('script[data-manager-evidence]')){const s=document.createElement('script');s.src='/manager-evidence.js';s.dataset.managerEvidence='1';document.body.appendChild(s)}
})();
