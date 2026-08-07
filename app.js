(() => {
  const state = JSON.parse(localStorage.getItem('opsreadyState') || '{}');
  if (!state.skills) state.skills = {
    Streaming: 91, Snowflake: 86, Databricks: 90, 'Data Quality': 94,
    Reconciliation: 93, FinOps: 78, 'Incident Response': 87, Security: 88,
    'Agents / ML': 82
  };
  if (!state.sopAck) state.sopAck = {};
  if (!state.customDrills) state.customDrills = [];
  if (!state.role) state.role = 'engineer';

  const save = () => localStorage.setItem('opsreadyState', JSON.stringify(state));
  const $ = id => document.getElementById(id);

  const views = [...document.querySelectorAll('.view')];
  function showView(id) {
    views.forEach(v => v.classList.toggle('active', v.id === id));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.toggle('active', n.dataset.view === id));
    window.scrollTo({top: 0, behavior: 'smooth'});
  }
  document.querySelectorAll('.nav-item').forEach(btn => btn.addEventListener('click', () => showView(btn.dataset.view)));
  document.querySelectorAll('.jump-btn').forEach(btn => btn.addEventListener('click', () => showView(btn.dataset.jump)));

  function renderRole() {
    const manager = state.role === 'manager';
    document.querySelectorAll('.manager-only').forEach(x => x.classList.toggle('hidden', !manager));
    $('roleToggle').textContent = manager ? 'Switch to Engineer View' : 'Switch to Manager View';
    if (!manager && $('manager').classList.contains('active')) showView('dashboard');
  }
  $('roleToggle').addEventListener('click', () => {
    state.role = state.role === 'manager' ? 'engineer' : 'manager';
    save(); renderRole();
  });

  function renderSkills() {
    const host = $('skillHeatmap'); host.innerHTML = '';
    Object.entries(state.skills).forEach(([name, score]) => {
      const row = document.createElement('div'); row.className = 'skill-row';
      row.innerHTML = `<span>${name}</span><div class="skill-track"><div class="skill-fill" style="width:${score}%"></div></div><strong>${score}%</strong>`;
      host.appendChild(row);
    });
    const vals = Object.values(state.skills);
    const avg = Math.round(vals.reduce((a,b)=>a+b,0)/vals.length);
    $('overallScore').textContent = avg + '%';
    $('overallRing').style.background = `conic-gradient(var(--accent) 0 ${avg}%, #20344e ${avg}% 100%)`;
    $('readinessLabel').textContent = avg >= 90 ? 'Top-Tier Ready' : avg >= 85 ? 'Production Ready' : 'Targeted Practice Needed';
    $('costScore').textContent = state.skills.FinOps + '%';
    $('reliabilityScore').textContent = Math.round((state.skills['Data Quality'] + state.skills.Reconciliation + state.skills['Incident Response'])/3) + '%';
    const weak = Object.entries(state.skills).sort((a,b)=>a[1]-b[1])[0];
    $('nextAction').innerHTML = `<strong>${weak[0]} is the current weakest domain at ${weak[1]}%.</strong><p>Run a targeted drill before the next full incident simulation. Readiness standard: explain the invariant, quantify the failure, fix the constrained layer, and prove the repair.</p>`;
  }

  const sops = [
    ['SOP-DR-001','Data Publication Acceptance','A successful job is not trusted publication. Freshness, quality, reconciliation and business invariants must pass.'],
    ['SOP-DR-002','Idempotent Recovery','Retries, replays and backfills must not create a second business effect. Deterministic keys and bounded replay are mandatory.'],
    ['SOP-DR-003','Streaming Reliability','Event-time semantics, checkpoint ownership, watermarks, state growth and late-event correction must be explicit.'],
    ['SOP-DR-004','Query & Compute Efficiency','Fix pruning, join cardinality, repeated scans and bad plans before using compute scaling as the primary solution.'],
    ['SOP-DR-005','Incident Evidence Preservation','Contain unsafe output first. Preserve checkpoints, offsets, query IDs, logs and the timeline before destructive recovery.'],
    ['SOP-DR-006','Agent / Automation Authority','Automation may execute bounded low-risk actions. High-impact financial, customer, security or compliance actions require authorization.']
  ];
  function renderSops() {
    const host = $('sopList'); host.innerHTML = '';
    sops.forEach(([id,title,desc]) => {
      const card = document.createElement('article'); card.className='sop-card';
      const checked = !!state.sopAck[id];
      card.innerHTML = `<span class="pill">${id}</span><h3>${title}</h3><p class="muted">${desc}</p>
        <label class="check-row"><input type="checkbox" ${checked?'checked':''}/><span>I acknowledge this standard and can explain how it is validated in production.</span></label>`;
      card.querySelector('input').addEventListener('change', e => {state.sopAck[id]=e.target.checked; save();});
      host.appendChild(card);
    });
  }

  function renderSims() {}

  $('gradeWeekly').addEventListener('click', () => {
    const math = $('lagMath').value.replace(/,/g,'').toLowerCase();
    const mathOk = math.includes('3000') || math.includes('3k');
    const layerOk = $('lagLayer').value.includes('Databricks');
    const inv = $('lagInvariant').value.toLowerCase();
    const invOk = (inv.includes('process') || inv.includes('throughput')) && (inv.includes('input') || inv.includes('arrival') || inv.includes('keep up'));
    const points = [mathOk,layerOk,invOk].filter(Boolean).length;
    const score = Math.round(points/3*100);
    state.skills.Streaming = Math.round((state.skills.Streaming + score)/2);
    state.skills.Databricks = Math.round((state.skills.Databricks + score)/2);
    state.weeklyDone = true; save(); renderSkills();
    $('weeklyStatus').textContent='Complete';
    $('weeklyFeedback').classList.remove('hidden');
    $('weeklyFeedback').innerHTML = `<strong>${score}%</strong><p>Expected math: backlog grows by 3,000 events/sec. First investigate the stream-processing path and partition skew because the Snowflake sink is normal. Invariant: sustained processing must meet or exceed sustained arrival while preserving correctness.</p>`;
  });

  $('gradeMonthly').addEventListener('click', () => {
    const containOk = $('containment').value.includes('Contain unsafe');
    const order = $('repairOrder').value.toLowerCase();
    const orderOk = order.includes('contain') && (order.includes('snapshot') || order.includes('evidence')) && order.includes('replay') && order.includes('recon');
    const ev = $('acceptanceEvidence').value.toLowerCase();
    const evOk = ev.includes('duplicate') && (ev.includes('count') || ev.includes('key')) && (ev.includes('lag') || ev.includes('latency')) && (ev.includes('point') || ev.includes('dollar') || ev.includes('residual'));
    const score = Math.round([containOk,orderOk,evOk].filter(Boolean).length/3*100);
    state.skills['Incident Response'] = Math.round((state.skills['Incident Response']+score)/2);
    state.skills.Reconciliation = Math.round((state.skills.Reconciliation+score)/2);
    state.monthlyDone=true; save(); renderSkills(); $('monthlyStatus').textContent='Complete';
    $('monthlyFeedback').classList.remove('hidden');
    $('monthlyFeedback').innerHTML=`<strong>${score}%</strong><p>Strong recovery order: contain customer-facing effects → preserve evidence → diagnose each control point → repair hot key/stream/sink/incremental/serving logic → bounded idempotent replay → reconcile counts, keys, points/dollars and latency → reopen only after acceptance gates pass.</p>`;
  });

  $('gradeFinops').addEventListener('click', () => {
    const a = $('finopsAction').value.includes('Inspect query profile');
    const p = $('finopsPlan').value.toLowerCase();
    const pOk = (p.includes('prun') || p.includes('join') || p.includes('scan')) && (p.includes('right') || p.includes('size') || p.includes('warehouse'));
    const score = Math.round([a,pOk].filter(Boolean).length/2*100);
    state.skills.FinOps = Math.round((state.skills.FinOps+score)/2); save(); renderSkills();
    $('finopsFeedback').classList.remove('hidden');
    $('finopsFeedback').innerHTML=`<strong>${score}%</strong><p>Correct principle: fix scan efficiency and join pathology first, then right-size the warehouse from the corrected workload. Cost optimization is valid only if correctness and SLA remain satisfied.</p>`;
  });

  $('generateTraining').addEventListener('click', () => {
    const drill = {
      title:$('incTitle').value || 'Untitled incident',
      impact:$('incImpact').value || 'Business impact not entered',
      root:$('incRoot').value || 'Root cause not entered',
      invariant:$('incInvariant').value || 'Invariant not entered',
      lesson:$('incLesson').value || 'Recovery lesson not entered'
    };
    state.customDrills.push(drill); save();
    $('generatedDrill').classList.remove('hidden');
    $('generatedDrill').innerHTML=`<span class="pill">Future Drill Created</span><h3>${drill.title}</h3><p><strong>Scenario:</strong> ${drill.impact}</p><p><strong>Question:</strong> Diagnose the root cause and state the invariant that must remain true.</p><p><strong>Expected root cause:</strong> ${drill.root}</p><p><strong>Expected lesson:</strong> ${drill.lesson}</p>`;
  });

  if (state.weeklyDone) $('weeklyStatus').textContent='Complete';
  if (state.monthlyDone) $('monthlyStatus').textContent='Complete';

  renderRole(); renderSkills(); renderSops(); renderSims();
})();
