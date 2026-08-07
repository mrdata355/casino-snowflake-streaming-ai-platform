(() => {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const norm = (s) => String(s || '').toLowerCase().replace(/\s+/g, ' ');
  const any = (text, choices) => choices.some((x) => norm(text).includes(norm(x)));
  let state;
  try { state = JSON.parse(localStorage.getItem('opsreadyV6') || '{}'); } catch (_) { state = {}; }
  state.best ||= { Snowflake: {}, Databricks: {}, 'SQL Server': {} };
  state.history ||= [];
  const save = () => localStorage.setItem('opsreadyV6', JSON.stringify(state));
  const active = {};

  async function loadTaskBank() {
    // The original V6 script remains the canonical task bank. We evaluate only the
    // declaration portion of that same-origin static asset and stop before its old renderer.
    const response = await fetch('/simulators/v6-full-job-cycle-lab.js', { cache: 'no-store' });
    if (!response.ok) throw new Error(`Task bank HTTP ${response.status}`);
    const source = await response.text();
    const marker = source.indexOf('function avg(');
    if (marker < 0) throw new Error('V6 task-bank marker not found.');
    const declarations = source.slice(0, marker);
    const expose = `${declarations}\nwindow.__OPSREADY_V6_BANK={sf,dbx,sql,cycle};\n})();`;
    // Source is bundled with this application, never user supplied.
    Function(expose)();
    if (!window.__OPSREADY_V6_BANK) throw new Error('V6 task bank failed to initialize.');
    return window.__OPSREADY_V6_BANK;
  }

  const avg = (obj) => {
    const values = Object.values(obj || {});
    return values.length ? Math.round(values.reduce((a, b) => a + b, 0) / values.length) : 0;
  };
  const master = () => {
    const values = [avg(state.best.Snowflake), avg(state.best.Databricks), avg(state.best['SQL Server'])].filter(Boolean);
    return values.length ? Math.round(values.reduce((a, b) => a + b, 0) / values.length) : 0;
  };
  function renderMaster() {
    $('master').textContent = `${master()}%`;
    $('masterSub').textContent = `Snowflake ${avg(state.best.Snowflake)}% • Databricks ${avg(state.best.Databricks)}% • SQL Server ${avg(state.best['SQL Server'])}%`;
  }
  function record(platform, task, score, evidence = 'simulated rubric') {
    state.best[platform][task.id] = Math.max(state.best[platform][task.id] || 0, score);
    state.history.push({ platform, title: task.title, task_id: task.id, score, evidence, at: new Date().toISOString() });
    state.history = state.history.slice(-150);
    save();
    renderMaster();
    try {
      parent.postMessage({ type: 'opsready-lab-score', lab: 'V6 Full Job-Cycle Lab', score: master(), detail: `${platform}: ${task.title} ${score}% • ${evidence}` }, '*');
    } catch (_) {}
  }

  function gradeTask(platform, task, work) {
    const code = work.querySelector('.task-code').value;
    const reason = work.querySelector('.task-reason').value;
    const checks = task.req.map((group) => ({ ok: any(code, group), label: group.join(' / ') }));
    const build = Math.round(70 * checks.filter((x) => x.ok).length / checks.length);
    const reasoning = Math.min(20,
      (any(reason, task.why) ? 12 : 0) +
      (any(reason, ['proof', 'validate', 'reconcile', 'metric', 'test', 'plan', 'profile', 'sla', 'tradeoff', 'failure']) ? 8 : 0)
    );
    const penalty = task.anti.reduce((sum, item) => sum + (any(code, [item[0]]) ? 10 : 0), 0);
    const safety = Math.max(0, 10 - penalty);
    const score = Math.max(0, Math.min(100, build + reasoning + safety));
    const output = work.querySelector('.task-output');
    output.textContent = `${score >= 80 ? 'SIMULATION ACCEPTED' : 'SIMULATION INCOMPLETE'}\n${task.out}\nBuild ${build}/70 • Reasoning ${reasoning}/20 • Safety ${safety}/10`;
    const feedback = work.querySelector('.task-feedback');
    feedback.className = `feedback ${score >= 80 ? 'pass' : score >= 60 ? 'partial' : 'fail'} task-feedback`;
    feedback.innerHTML = `<b>${score}%</b><div class="rubric">${checks.map((x) => `<div class="row ${x.ok ? 'ok' : 'bad'}">${x.ok ? '✓' : '✗'} ${x.label}</div>`).join('')}</div><p><b>Reasoning target:</b> ${task.why.join(' • ')}</p>${penalty ? '<p class="bad">Anti-pattern penalty applied.</p>' : ''}`;
    record(platform, task, score);
    return score;
  }

  function renderPlatform(tasks, platform, listId, workId) {
    const list = $(listId);
    const work = $(workId);
    active[platform] = tasks[0];

    function drawList() {
      list.innerHTML = '';
      tasks.forEach((task) => {
        const button = document.createElement('button');
        const score = state.best[platform][task.id] || 0;
        button.className = `${active[platform] === task ? 'active ' : ''}${score >= 80 ? 'pass' : ''}`;
        button.dataset.taskId = task.id;
        button.dataset.wired = 'true';
        button.innerHTML = `<b>${task.title}</b><small>${task.stage}${score ? ` • ${score}%` : ''}</small>`;
        button.addEventListener('click', () => {
          active[platform] = task;
          drawList();
          drawWork();
        });
        list.appendChild(button);
      });
    }

    function drawWork() {
      const task = active[platform];
      work.dataset.platform = platform;
      work.dataset.taskId = task.id;
      work.innerHTML = `
        <div class="meta"><span class="pill">${platform}</span><span class="pill">${task.stage}</span><span class="pill">Build + reasoning</span></div>
        <h2>${task.title}</h2>
        <div class="brief">${task.brief}</div>
        <div class="why"><b>Engineer defense required:</b> explain why this implementation fits the workload, what alternative you rejected, and how you prove it is safe/correct.</div>
        <div class="terminal">
          <div class="terminal-bar">${platform} training console • simulation + optional real sandbox</div>
          <textarea class="task-code">${task.starter}</textarea>
          <div class="actions">
            <button class="primary task-grade" type="button">Run & Grade Simulation</button>
            <button class="task-reset" type="button">Reset starter</button>
            <button class="task-live" type="button">Execute in Real Sandbox</button>
          </div>
          <div class="output task-output">Ready. Simulation changes no production resource. Real execution requires a configured isolated gateway session.</div>
        </div>
        <label><b>Why this approach / why not the alternative?</b></label>
        <textarea class="task-reason" style="width:100%;min-height:95px;background:#07121f;color:#eef7ff;border:1px solid #29445f;border-radius:9px;padding:10px" placeholder="State workload fit, tradeoff/failure mode, and proof of correctness..."></textarea>
        <div class="task-feedback"></div>`;
      const grade = work.querySelector('.task-grade');
      const reset = work.querySelector('.task-reset');
      const live = work.querySelector('.task-live');
      [grade, reset, live].forEach((b) => b.dataset.wired = 'true');
      reset.addEventListener('click', () => {
        work.querySelector('.task-code').value = task.starter;
        work.querySelector('.task-output').textContent = 'Starter restored.';
      });
      grade.addEventListener('click', () => { gradeTask(platform, task, work); drawList(); });
      live.addEventListener('click', () => {
        document.dispatchEvent(new CustomEvent('opsready:v6-live-execute', { detail: { platform, taskId: task.id } }));
      });
      document.dispatchEvent(new CustomEvent('opsready:v6-task-rendered', { detail: { platform, taskId: task.id } }));
    }

    drawList();
    drawWork();
  }

  function dashboard() {
    const rows = [
      ['Snowflake', avg(state.best.Snowflake), `${Object.keys(state.best.Snowflake).length}/20`],
      ['Databricks', avg(state.best.Databricks), `${Object.keys(state.best.Databricks).length}/20`],
      ['SQL Server', avg(state.best['SQL Server']), `${Object.keys(state.best['SQL Server']).length}/18`],
      ['Overall', master(), `${state.history.length} attempts`]
    ];
    $('summary').innerHTML = rows.map((r) => `<article class="card"><span>${r[0]}</span><strong>${r[1]}%</strong><small>${r[2]}</small></article>`).join('');
    $('history').innerHTML = state.history.slice().reverse().slice(0, 40).map((h) => `<tr><td>${h.platform}</td><td>${h.title}</td><td>${h.score}%</td><td>${new Date(h.at).toLocaleString()}</td></tr>`).join('') || '<tr><td colspan="4">No graded work yet.</td></tr>';
  }

  function current(platform) {
    const mapping = { Snowflake: 'sfWork', Databricks: 'dbxWork', 'SQL Server': 'sqlWork' };
    const work = $(mapping[platform]);
    const task = active[platform];
    if (!work || !task) return null;
    return {
      platform,
      task,
      code: work.querySelector('.task-code')?.value || '',
      reason: work.querySelector('.task-reason')?.value || '',
      work,
    };
  }

  window.OpsReadyV6 = {
    current,
    recordLive(platform, taskId, success, detail) {
      const task = active[platform];
      if (!task || task.id !== taskId) return;
      const evidenceScore = success ? 100 : 0;
      if (success) record(platform, task, Math.max(state.best[platform][task.id] || 0, 90), `real sandbox: ${detail || 'execution succeeded'}`);
      const work = current(platform)?.work;
      if (work) {
        const fb = work.querySelector('.task-feedback');
        if (fb) {
          fb.className = `feedback ${success ? 'pass' : 'fail'} task-feedback`;
          fb.innerHTML = `<b>${success ? 'REAL EXECUTION VERIFIED' : 'REAL EXECUTION FAILED'}</b><p>${detail || ''}</p>`;
        }
      }
      return evidenceScore;
    },
    master,
    dashboard,
  };

  loadTaskBank().then(({ sf, dbx, sql, cycle }) => {
    renderPlatform(sf, 'Snowflake', 'sfList', 'sfWork');
    renderPlatform(dbx, 'Databricks', 'dbxList', 'dbxWork');
    renderPlatform(sql, 'SQL Server', 'sqlList', 'sqlWork');
    $('cycleGrid').innerHTML = cycle.map((text, i) => `<article class="card"><div class="num">${String(i + 1).padStart(2, '0')}</div><h3>${text}</h3><p>${i < 3 ? 'Design before code.' : i < 9 ? 'Build with deterministic contracts and tests.' : i < 12 ? 'Operate for safe release, performance and observability.' : 'Recover with bounded actions and prove business correctness.'}</p></article>`).join('');
    document.querySelectorAll('#tabs button').forEach((button) => {
      button.dataset.wired = 'true';
      button.addEventListener('click', () => {
        document.querySelectorAll('#tabs button').forEach((x) => x.classList.remove('active'));
        document.querySelectorAll('.tab').forEach((x) => x.classList.remove('active'));
        button.classList.add('active');
        $(button.dataset.tab).classList.add('active');
        if (button.dataset.tab === 'dash') dashboard();
      });
    });
    $('reset').dataset.wired = 'true';
    $('reset').addEventListener('click', () => {
      if (confirm('Reset V6 progress?')) {
        localStorage.removeItem('opsreadyV6');
        localStorage.removeItem('opsreadyV6LiveEvidence');
        location.reload();
      }
    });
    renderMaster();
    document.dispatchEvent(new Event('opsready:v6-ready'));
  }).catch((error) => {
    document.body.innerHTML = `<main style="padding:24px"><h1>V6 failed to initialize</h1><pre>${String(error)}</pre></main>`;
  });
})();
