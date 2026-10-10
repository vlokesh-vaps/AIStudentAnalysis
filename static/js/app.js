(() => {
  const state = { students: [], classAnalysis: null, studentAnalysis: null, sort: { key: 'name', direction: 1 } };
  const $ = (id) => document.getElementById(id);
  const fileInput = $('file-input');
  const dropZone = $('drop-zone');

  function getAppConfig() {
    if (window.__APP_CONFIG__) {
      return window.__APP_CONFIG__;
    }
    const configEl = document.getElementById('app-config');
    if (configEl && configEl.textContent) {
      try {
        return JSON.parse(configEl.textContent);
      } catch (_e) {
        // ignore JSON parse error
      }
    }
    const metaBase = document.querySelector('meta[name="app-base"]')?.getAttribute('content');
    const basePath = (metaBase !== null && metaBase !== undefined) ? metaBase : '';
    return {
      basePath: basePath,
      apiPrefix: (basePath ? basePath.replace(/\/+$/, '') : '') + '/api',
      docsUrl: ''
    };
  }

  function resolveApiUrl(endpoint) {
    const config = getAppConfig();
    const basePath = (config.basePath || '').trim().replace(/\/+$/, '');
    let path = String(endpoint || '').trim();

    // If fully qualified external URL, preserve as-is
    if (/^https?:\/\//i.test(path)) {
      return path;
    }

    if (!path.startsWith('/')) {
      path = '/' + path;
    }

    // Handle basePath deduplication
    if (basePath) {
      if (path === basePath) {
        return path;
      }
      if (path.startsWith(basePath + '/')) {
        // Strip duplicate repetitions of basePath if any
        while (path.startsWith(basePath + basePath + '/')) {
          path = path.slice(basePath.length);
        }
        return path;
      }
    }

    // If path starts with /api
    if (path.startsWith('/api')) {
      return basePath ? `${basePath}${path}` : path;
    }

    // Default to routing via API prefix
    const apiBase = config.apiPrefix ? config.apiPrefix.replace(/\/+$/, '') : `${basePath}/api`;
    return `${apiBase}${path}`;
  }

  function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
  }

  function toast(message, type = 'success') {
    const id = `toast-${Date.now()}`;
    $('toast-container').insertAdjacentHTML('beforeend', `<div id="${id}" class="toast text-bg-${type === 'error' ? 'danger' : 'success'}" role="status"><div class="d-flex"><div class="toast-body">${escapeHtml(message)}</div><button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button></div></div>`);
    const element = $(id);
    const instance = new bootstrap.Toast(element, { delay: 4200 });
    element.addEventListener('hidden.bs.toast', () => element.remove());
    instance.show();
  }

  async function api(url, options) {
    const targetUrl = resolveApiUrl(url);
    try {
      const response = await fetch(targetUrl, options);
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload.error || payload.message || `Request failed with status ${response.status}`);
      }
      return payload;
    } catch (err) {
      if (err instanceof TypeError && err.message === 'Failed to fetch') {
        throw new Error('Unable to reach the server. Please check your network connection.');
      }
      throw err;
    }
  }

  function buttonBusy(button, busy) {
    button.disabled = busy;
    button.querySelector('.spinner-border')?.classList.toggle('d-none', !busy);
    const label = button.querySelector('.button-label');
    if (label) label.classList.toggle('opacity-75', busy);
  }

  async function upload(file) {
    if (!file) return;
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['csv', 'xlsx', 'xls', 'pdf'].includes(ext)) {
      toast('Please choose a CSV, Excel, or PDF file.', 'error');
      return;
    }
    $('upload-progress').classList.remove('d-none');
    $('upload-success').classList.add('d-none');
    try {
      const form = new FormData();
      form.append('file', file);
      const data = await api('/api/upload', { method: 'POST', body: form });
      if (!data.students?.length) throw new Error('No valid student data found. Please check the file format.');
      state.students = data.students;
      state.classAnalysis = null;
      state.studentAnalysis = null;
      $('sample-box').classList.add('d-none');
      $('upload-success').classList.remove('d-none');
      $('data-panel').classList.remove('d-none');
      $('class-panel').classList.add('d-none');
      $('student-panel').classList.remove('d-none');
      renderStudents();
      populateSelect();
      $('student-results').replaceChildren();
      toast(`Loaded ${state.students.length} students`);
      $('data-panel').scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (error) {
      toast(error.message, 'error');
    } finally {
      $('upload-progress').classList.add('d-none');
      fileInput.value = '';
    }
  }

  function sortedStudents() {
    return [...state.students].sort((a, b) => {
      const getValue = student => {
        if (['name', 'totalScore', 'averageScore'].includes(state.sort.key)) return student[state.sort.key];
        return (student.subjects || []).find(subject => subject.subject === state.sort.key)?.score ?? -Infinity;
      };
      const x = getValue(a), y = getValue(b);
      const result = typeof x === 'string' ? x.localeCompare(y) : Number(x) - Number(y);
      return result * state.sort.direction;
    });
  }

  function renderStudents() {
    $('student-count').textContent = `${state.students.length} students found`;
    const subjects = [...new Set(state.students.flatMap(student => (student.subjects || []).map(subject => subject.subject)))];
    const columns = [['name', 'Student Name'], ...subjects.map(subject => [subject, subject]), ['totalScore', 'Total'], ['averageScore', 'Average']];
    $('students-thead').innerHTML = `<tr>${columns.map(([key, title]) => `<th><button class="sort-button" data-sort="${escapeHtml(key)}">${escapeHtml(title)}${state.sort.key === key ? (state.sort.direction > 0 ? ' ↑' : ' ↓') : ''}</button></th>`).join('')}</tr>`;
    $('students-tbody').innerHTML = sortedStudents().map(student => `<tr><td class="fw-semibold">${escapeHtml(student.name)}</td>${subjects.map(name => { const found = (student.subjects || []).find(s => s.subject === name); return `<td>${found ? escapeHtml(found.score) : '<span class="text-body-tertiary">—</span>'}</td>`; }).join('')}<td>${escapeHtml(student.totalScore)}</td><td><span class="score-pill">${escapeHtml(student.averageScore)}%</span></td></tr>`).join('');
    $('students-thead').querySelectorAll('[data-sort]').forEach(button => button.addEventListener('click', () => {
      const key = button.dataset.sort;
      state.sort = { key, direction: state.sort.key === key ? -state.sort.direction : (key === 'name' ? 1 : -1) };
      renderStudents();
    }));
  }

  function populateSelect() {
    const select = $('student-select');
    select.innerHTML = '<option value="">Select a student…</option>' + state.students.map((student, index) => `<option value="${index}">${escapeHtml(student.name)} (Avg: ${escapeHtml(student.averageScore)}%)</option>`).join('');
    $('student-button').disabled = true;
  }

  function performerCard(person, type) {
    const extraLabel = type === 'top' ? 'Praise' : 'Recommendations';
    const extra = type === 'top' ? person.praise : person.recommendations;
    return `<article class="performer-card ${type}"><div class="d-flex justify-content-between gap-2"><span class="performer-name">${escapeHtml(person.name)}</span><span class="performer-scores">Avg ${escapeHtml(person.averageScore)}% · Total ${escapeHtml(person.totalScore)}</span></div><p>${escapeHtml(person.analysis)}</p>${extra ? `<p class="${type === 'top' ? 'praise' : 'recommendation'}"><strong>${extraLabel}:</strong> ${escapeHtml(extra)}</p>` : ''}</article>`;
  }

  async function analyzeClass() {
    const button = $('class-button');
    buttonBusy(button, true);
    try {
      const result = await api('/api/analyze/class', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ students: state.students }) });
      state.classAnalysis = result;
      renderClass(result);
      $('class-panel').classList.remove('d-none');
      bootstrap.Collapse.getOrCreateInstance($('class-content'), { toggle: false }).show();
      toast('Class analysis complete');
      $('class-panel').scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (error) {
      toast(error.message, 'error');
    } finally {
      buttonBusy(button, false);
    }
  }

  function renderClass(result) {
    $('class-results').innerHTML = `<div class="analysis-overview"><h3>Class overview</h3><div>${escapeHtml(result.classOverview)}</div></div><div class="row g-4 performer-grid"><div class="col-lg-6"><h3 class="performer-list-title">🏅 Top Performers</h3>${(result.topPerformers || []).map(p => performerCard(p, 'top')).join('')}</div><div class="col-lg-6"><h3 class="performer-list-title">🌱 Weak Performers</h3>${(result.weakPerformers || []).map(p => performerCard(p, 'weak')).join('')}</div></div>`;
  }

  function listBlock(title, items, textKey, labelKey = 'name') {
    if (!items?.length) return '';
    return `<div class="list-section"><h4>${escapeHtml(title)}</h4><div class="row g-2">${items.map(item => `<div class="col-md-6"><div class="result-card mb-0"><h3>${escapeHtml(item[labelKey])}${item.score != null ? ` <span class="text-secondary fw-normal">· ${escapeHtml(item.score)}%</span>` : ''}</h3><p>${escapeHtml(item[textKey])}</p></div></div>`).join('')}</div></div>`;
  }

  function bulletBlock(title, items) {
    if (!items?.length) return '';
    return `<div class="list-section"><h4>${escapeHtml(title)}</h4><ul>${items.map(item => `<li>${escapeHtml(item)}</li>`).join('')}</ul></div>`;
  }

  function trajectoryClass(value) {
    return String(value || '').toLowerCase().replace(/[^a-z]+/g, '-').replace(/^-|-$/g, '');
  }

  function renderStudent(result) {
    const weak = result.weakestSubject || {};
    const prediction = result.performancePrediction || {};
    const subjectScores = prediction.predictedSubjectScores || [];
    $('student-results').innerHTML = `<div class="student-result-grid"><div class="result-card"><h3>Weakest Subject · ${escapeHtml(weak.name)} <span class="text-secondary fw-normal">${escapeHtml(weak.score)}%</span></h3><p>${escapeHtml(weak.analysis)}</p></div><div class="row g-3"><div class="col-lg-6">${listBlock('Subjects Needing Improvement', result.needsImprovement, 'recommendation')}</div><div class="col-lg-6">${listBlock('Strong Subjects', result.strongSubjects, 'praise')}</div></div><div class="row g-3 mt-1"><div class="col-lg-6"><div class="result-card h-100"><h3>Overall Assessment</h3><p>${escapeHtml(result.overallAssessment)}</p></div></div><div class="col-lg-6"><div class="result-card h-100"><h3>Improvement Strategy</h3><p>${escapeHtml(result.improvementStrategy)}</p></div></div></div><section class="prediction-card mt-3"><div class="prediction-head"><div><h3>Performance Prediction</h3><div class="prediction-range mt-2">${escapeHtml(prediction.predictedScoreRange || '—')}</div><div class="prediction-meta">Confidence: ${escapeHtml(prediction.confidenceLevel || '—')}</div></div><span class="trajectory ${trajectoryClass(prediction.trajectory)}">${escapeHtml(prediction.trajectory || '—')}</span></div><div class="table-responsive mt-3"><table class="table prediction-table align-middle mb-0"><thead><tr><th>Subject</th><th>Predicted</th><th>Potential</th><th>Comparison</th></tr></thead><tbody>${subjectScores.map(item => `<tr><td>${escapeHtml(item.subject)}</td><td>${escapeHtml(item.predictedScore)}%</td><td>${escapeHtml(item.potentialScore)}%</td><td><div class="mini-bars" title="Predicted and potential score"><span class="predicted" style="flex:${Math.max(1, Number(item.predictedScore) || 0)}"></span><span class="potential" style="flex:${Math.max(1, (Number(item.potentialScore) || 0) - (Number(item.predictedScore) || 0))}"></span></div></td></tr>`).join('')}</tbody></table></div><div class="row g-3">${[['Key Risk Factors', prediction.keyRiskFactors], ['Growth Opportunities', prediction.growthOpportunities], ['Actionable Milestones', prediction.actionableMilestones]].map(([title, list]) => `<div class="col-md-4">${bulletBlock(title, list)}</div>`).join('')}</div></section></div>`;
  }

  async function analyzeStudent() {
    const selected = $('student-select').value;
    if (selected === '') return;
    const student = state.students[Number(selected)];
    const button = $('student-button');
    buttonBusy(button, true);
    try {
      const result = await api('/api/analyze/student', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ student }) });
      state.studentAnalysis = result;
      renderStudent(result);
      toast(`Analysis for ${student.name} complete`);
    } catch (error) {
      toast(error.message, 'error');
    } finally {
      buttonBusy(button, false);
      button.disabled = !$('student-select').value;
    }
  }

  fileInput.addEventListener('change', () => upload(fileInput.files[0]));
  $('browse-placeholder')?.addEventListener('click', () => fileInput.click());
  ['dragenter', 'dragover'].forEach(eventName => dropZone.addEventListener(eventName, event => { event.preventDefault(); dropZone.classList.add('drag-over'); }));
  ['dragleave', 'drop'].forEach(eventName => dropZone.addEventListener(eventName, event => { event.preventDefault(); dropZone.classList.remove('drag-over'); }));
  dropZone.addEventListener('drop', event => upload(event.dataTransfer.files[0]));
  $('class-button').addEventListener('click', analyzeClass);
  $('student-select').addEventListener('change', () => { $('student-button').disabled = !$('student-select').value; $('student-results').replaceChildren(); });
  $('student-button').addEventListener('click', analyzeStudent);

  // Synchronize docs link if rendered
  const config = getAppConfig();
  const docsLink = $('docs-link');
  if (docsLink && config.docsUrl) {
    docsLink.href = config.docsUrl;
  }
})();
