(() => {
  const state = JSON.parse(localStorage.getItem('opsreadyState') || '{}');
  if (!state.skills) state.skills = {
    Streaming: 91, Snowflake: 86, Databricks: 90, 'Data Quality': 94,
    Reconciliation: 93, FinOps: 78, 'Incident Response': 87, Security: 88,
    'Agents / ML': 82
  };
  if (!state.sopAck) state.sopAck = {};
  if (!state.customDrills) state.customDrills = [];
  if (!state.gradeHistory) state.gradeHistory = [];
  if (!state.role) state.role = 'engineer';

  const save = () => localStorage.setItem('opsreadyState', JSON.stringify(state));
  const $ = id => document.getElementById(id);
  const safe = id => document.getElementById(id);
  const norm = s => (s || '').toLowerCase().replace(/[^a-z0-9><=+./$%\s-]/g,' ').replace(/\s+/g,' ').trim();
  const hasAny = (text, words) => words.some(w => norm(text).includes(norm(w)));
  const hasGroup = (text, group) => hasAny(text, group);
  const pct = (earned, possible) => possible ? Math.round((earned / possible) * 100) : 0;
  const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  function rubricScore(text, criteria) {
    let earned = 0;
    const rows = criteria.map(c => {
      const ok = c.groups.every(group => hasGroup(text, group));
      if (ok) earned += c.points;
      return { ...c, ok };
    });
    return { earned, possible: criteria.reduce((a,c)=>a+c.points,0), rows };
  }

  function breakdownHtml(title, score, items, expected) {
    const lines = items.map(i => `<li style="margin:6px 0"><strong>${i.ok ? '✓' : '✗'} ${esc(i.label)}</strong>${i.note ? ` — ${esc(i.note)}` : ''}</li>`).join('');
    return `<div style="font-size:28px;font-weight:800;margin-bottom:8px">${score}%</div><strong>${esc(title)}</strong><ul style="padding-left:20px">${lines}</ul><div style="margin-top:10px"><strong>Reference answer:</strong><p>${esc(expected)}</p></div>`;
  }

  function recordGrade(name, score) {
    state.gradeHistory.push({name, score, at: new Date().toISOString()});
    state.gradeHistory = state.gradeHistory.slice(-50);
    save();
  }

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
    if (safe('roleToggle')) $('roleToggle').textContent = manager ? 'Switch to Engineer View' : 'Switch to Manager View';
    if (!manager && safe('manager') && $('manager').classList.contains('active')) showView('dashboard');
  }
  if (safe('roleToggle')) $('roleToggle').addEventListener('click', () => {
    state.role = state.role === 'manager' ? 'engineer' : 'manager';
    save(); renderRole();
  });

  function renderSkills() {
    const host = safe('skillHeatmap');
    if (!host) return;
    host.innerHTML = '';
    Object.entries(state.skills).forEach(([name, score]) => {
      const row = document.createElement('div'); row.className = 'skill-row';
      row.innerHTML = `<span>${name}</span><div class="skill-track"><div class="skill-fill" style="width:${score}%"></div></div><strong>${score}%</strong>`;
      host.appendChild(row);
    });
    const vals = Object.values(state.skills);
    const avg = Math.round(vals.reduce((a,b)=>a+b,0)/vals.length);
    if (safe('overallScore')) $('overallScore').textContent = avg + '%';
    if (safe('overallRing')) $('overallRing').style.background = `conic-gradient(var(--accent) 0 ${avg}%, #20344e ${avg}% 100%)`;
    if (safe('readinessLabel')) $('readinessLabel').textContent = avg >= 90 ? 'Top-Tier Ready' : avg >= 85 ? 'Production Ready' : 'Targeted Practice Needed';
    if (safe('costScore')) $('costScore').textContent = state.skills.FinOps + '%';
    if (safe('reliabilityScore')) $('reliabilityScore').textContent = Math.round((state.skills['Data Quality'] + state.skills.Reconciliation + state.skills['Incident Response'])/3) + '%';
    const weak = Object.entries(state.skills).sort((a,b)=>a[1]-b[1])[0];
    if (safe('nextAction')) $('nextAction').innerHTML = `<strong>${weak[0]} is the current weakest domain at ${weak[1]}%.</strong><p>Run a targeted drill. You are graded on invariant, math, diagnosis, repair, recovery, and proof—not exact wording.</p>`;
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
    const host = safe('sopList'); if (!host) return;
    host.innerHTML = '';
    sops.forEach(([id,title,desc]) => {
      const card = document.createElement('article'); card.className='sop-card';
      const checked = !!state.sopAck[id];
      card.innerHTML = `<span class="pill">${id}</span><h3>${title}</h3><p class="muted">${desc}</p><label class="check-row"><input type="checkbox" ${checked?'checked':''}/><span>I acknowledge this standard and can explain how it is validated in production.</span></label>`;
      card.querySelector('input').addEventListener('change', e => {state.sopAck[id]=e.target.checked; save();});
      host.appendChild(card);
    });
  }
  function renderSims() {}

  if (safe('gradeWeekly')) $('gradeWeekly').addEventListener('click', () => {
    const rawMath = $('lagMath').value;
    const compact = rawMath.replace(/,/g,'').toLowerCase();
    const mathOk = /(^|\D)3000(\D|$)/.test(compact) || compact.includes('3k') || (compact.includes('14000') && compact.includes('11000'));
    const layerOk = $('lagLayer').value.includes('Databricks');
    const inv = $('lagInvariant').value;
    const invRubric = rubricScore(inv, [
      {label:'States processing/throughput requirement', points:20, groups:[['process','processing','throughput','consume']]},
      {label:'Compares processing with incoming/arrival rate', points:15, groups:[['input','incoming','arrival','ingest'],['meet','exceed','greater','keep up','>=','at least']]},
      {label:'Protects correctness while recovering', points:15, groups:[['correct','duplicate','idempot','business effect','integrity','ordering']]}
    ]);
    const earned = (mathOk?25:0) + (layerOk?25:0) + invRubric.earned;
    const score = pct(earned,100);
    state.skills.Streaming = Math.round((state.skills.Streaming + score)/2);
    state.skills.Databricks = Math.round((state.skills.Databricks + score)/2);
    state.weeklyDone = true;
    recordGrade('Weekly Streaming Lag Drill', score); renderSkills();
    if (safe('weeklyStatus')) $('weeklyStatus').textContent='Complete';
    const items = [
      {ok:mathOk,label:'Backlog growth math',note:'14,000 - 11,000 = 3,000 events/sec'},
      {ok:layerOk,label:'First constrained layer',note:'Databricks processing / partition skew because Snowflake sink is normal'},
      ...invRubric.rows
    ];
    $('weeklyFeedback').classList.remove('hidden');
    $('weeklyFeedback').innerHTML = breakdownHtml('Weekly drill graded', score, items, 'Backlog grows by 3,000 events/sec. Investigate Databricks processing and partition skew first. Invariant: sustained processing throughput must meet or exceed incoming throughput while preserving correctness and idempotent business effects.');
  });

  if (safe('gradeMonthly')) $('gradeMonthly').addEventListener('click', () => {
    const containOk = $('containment').value.includes('Contain unsafe');
    const order = $('repairOrder').value;
    const orderRubric = rubricScore(order, [
      {label:'Contain customer/business impact first',points:10,groups:[['contain','block','pause','stop publication','freeze']]},
      {label:'Preserve evidence / snapshot state',points:10,groups:[['snapshot','evidence','offset','checkpoint','logs','query id','preserve']]},
      {label:'Diagnose by control point / bottleneck',points:10,groups:[['diagnos','control point','bottleneck','root cause','localize','localise']]},
      {label:'Repair causal layers rather than scale blindly',points:10,groups:[['repair','fix','hot key','partition','merge','dbt','cache','sink']]},
      {label:'Use bounded idempotent replay',points:10,groups:[['replay','backfill'],['idempot','bounded','deterministic','interval']]},
      {label:'Reconcile before reopening',points:10,groups:[['reconcil','control total','residual'],['reopen','publish','acceptance','gate']]}
    ]);
    const ev = $('acceptanceEvidence').value;
    const evRubric = rubricScore(ev, [
      {label:'Duplicate/business-key verification',points:8,groups:[['duplicate','unique','reward id','business key']]},
      {label:'Counts / accepted-rejected controls',points:6,groups:[['count','accepted','rejected','source','target']]},
      {label:'Points/dollars/residual reconciliation',points:6,groups:[['point','dollar','amount','residual','ledger']]},
      {label:'Lag/throughput/freshness verification',points:5,groups:[['lag','throughput','freshness','backlog']]},
      {label:'Serving latency / smoke check',points:5,groups:[['latency','p95','api','serving','smoke']]}
    ]);
    const earned = (containOk?10:0) + orderRubric.earned + evRubric.earned;
    const score = pct(earned,100);
    state.skills['Incident Response'] = Math.round((state.skills['Incident Response']+score)/2);
    state.skills.Reconciliation = Math.round((state.skills.Reconciliation+score)/2);
    state.monthlyDone=true;
    recordGrade('Monthly Friday Night Cascade', score); renderSkills();
    if (safe('monthlyStatus')) $('monthlyStatus').textContent='Complete';
    const items = [
      {ok:containOk,label:'Contain unsafe reward publication first',note:'Do not scale/restart before customer impact is controlled'},
      ...orderRubric.rows,
      ...evRubric.rows
    ];
    $('monthlyFeedback').classList.remove('hidden');
    $('monthlyFeedback').innerHTML = breakdownHtml('Monthly incident graded', score, items, 'Contain unsafe reward publication → preserve evidence → diagnose each control point → repair hot-key/stream/Snowflake/dbt/serving defects in dependency order → bounded idempotent replay → reconcile counts, keys, points/dollars, duplicates, freshness and API p95 → reopen only after acceptance gates pass.');
  });

  if (safe('gradeFinops')) $('gradeFinops').addEventListener('click', () => {
    const actionOk = $('finopsAction').value.includes('Inspect query profile');
    const plan = $('finopsPlan').value;
    const planRubric = rubricScore(plan, [
      {label:'Inspect query profile / bytes scanned first',points:15,groups:[['profile','bytes','scan','query history']]},
      {label:'Address pruning/filter design',points:15,groups:[['prun','filter','micro-partition','predicate']]},
      {label:'Check join cardinality / explosion',points:15,groups:[['join','cardinality','cartesian','explosion']]},
      {label:'Right-size compute after query repair',points:15,groups:[['right-size','right size','warehouse','compute'],['after','then','once','corrected']]},
      {label:'Protect SLA and correctness',points:15,groups:[['sla','latency','correct','reliab','acceptance']]}
    ]);
    const cost = Number($('avoidableCost').value || 0);
    const costOk = cost > 0;
    const earned = (actionOk?20:0) + (costOk?5:0) + planRubric.earned;
    const score = pct(earned,100);
    state.skills.FinOps = Math.round((state.skills.FinOps+score)/2);
    recordGrade('FinOps Snowflake Cost Lab', score); renderSkills();
    const items = [
      {ok:actionOk,label:'First action is diagnosis, not warehouse scaling',note:'Inspect profile, pruning, joins, spills, and scans'},
      {ok:costOk,label:'Quantifies avoidable cost',note:'Any defensible positive estimate earns credit in this demo'},
      ...planRubric.rows
    ];
    $('finopsFeedback').classList.remove('hidden');
    $('finopsFeedback').innerHTML = breakdownHtml('FinOps lab graded', score, items, 'Inspect the query profile first. Fix pruning, predicate design, join cardinality, repeated scans and spills. Only then right-size compute from the corrected workload, and prove SLA/correctness remain within contract.');
  });

  if (safe('generateTraining')) $('generateTraining').addEventListener('click', () => {
    const drill = {
      title:$('incTitle').value || 'Untitled incident',
      impact:$('incImpact').value || 'Business impact not entered',
      root:$('incRoot').value || 'Root cause not entered',
      invariant:$('incInvariant').value || 'Invariant not entered',
      lesson:$('incLesson').value || 'Recovery lesson not entered'
    };
    state.customDrills.push(drill); save();
    $('generatedDrill').classList.remove('hidden');
    $('generatedDrill').innerHTML=`<span class="pill">Future Drill Created</span><h3>${esc(drill.title)}</h3><p><strong>Scenario:</strong> ${esc(drill.impact)}</p><p><strong>Question:</strong> Diagnose the root cause and state the invariant that must remain true.</p><p><strong>Expected root cause:</strong> ${esc(drill.root)}</p><p><strong>Expected invariant:</strong> ${esc(drill.invariant)}</p><p><strong>Expected lesson:</strong> ${esc(drill.lesson)}</p>`;
  });

  if (state.weeklyDone && safe('weeklyStatus')) $('weeklyStatus').textContent='Complete';
  if (state.monthlyDone && safe('monthlyStatus')) $('monthlyStatus').textContent='Complete';
  renderRole(); renderSkills(); renderSops(); renderSims();
})();
