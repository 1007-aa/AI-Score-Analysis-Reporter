/* ─────────────────────────────────────────────────────────
   Classes Report Generator — Frontend JS
   Handles: file uploads, drag-drop, student grid,
            SSE progress streaming, results rendering
   ───────────────────────────────────────────────────────── */

// ── State ─────────────────────────────────────────────────
const state = {
  students: [],
  selected: new Set(),
  generatedFiles: [],
  currentJobId: null,
};

// ── On load ───────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  checkApiHealth();
  wireInputs();
  wireDragDrop();
  setDefaultDate();
});

function setDefaultDate() {
  const el = document.getElementById('test-date');
  if (el) el.value = new Date().toISOString().split('T')[0];
}

// ── API Health Check ──────────────────────────────────────
async function checkApiHealth() {
  const dot  = document.getElementById('status-dot');
  const text = document.getElementById('status-text');
  try {
    const res  = await fetch('/health');
    const data = await res.json();
    if (data.groq_key_set) {
      dot.className = 'status-dot ok';
      text.textContent = 'Groq API Connected';
    } else {
      dot.className = 'status-dot fail';
      text.textContent = 'GROQ_API_KEY missing';
    }
  } catch {
    dot.className = 'status-dot fail';
    text.textContent = 'Dashboard offline';
  }
}

// ── Wire File Inputs ──────────────────────────────────────
function wireInputs() {
  const map = [
    { input: 'input-csv',      upload: uploadCsv,      status: 'csv-status',      drop: 'drop-csv' },
    { input: 'input-syllabus', upload: uploadSyllabus,  status: 'syllabus-status', drop: 'drop-syllabus' },
    { input: 'input-qp',       upload: uploadQp,        status: 'qp-status',       drop: 'drop-qp' },
  ];
  map.forEach(({ input, upload, status, drop }) => {
    const el = document.getElementById(input);
    if (el) el.addEventListener('change', () => upload(el.files[0], status, drop));
  });
}

// ── Drag-Drop ─────────────────────────────────────────────
function wireDragDrop() {
  wireDrop('drop-csv',      (f) => uploadCsv(f, 'csv-status', 'drop-csv'));
  wireDrop('drop-syllabus', (f) => uploadSyllabus(f, 'syllabus-status', 'drop-syllabus'));
  wireDrop('drop-qp',       (f) => uploadQp(f, 'qp-status', 'drop-qp'));
}

function wireDrop(zoneId, handler) {
  const zone = document.getElementById(zoneId);
  if (!zone) return;
  zone.addEventListener('dragover',  (e) => { e.preventDefault(); zone.classList.add('dragover'); });
  zone.addEventListener('dragleave', ()  => zone.classList.remove('dragover'));
  zone.addEventListener('drop', (e) => {
    e.preventDefault();
    zone.classList.remove('dragover');
    const file = e.dataTransfer?.files?.[0];
    if (file) handler(file);
  });
}

// ── Upload: CSV ───────────────────────────────────────────
async function uploadCsv(file, statusId, dropId) {
  if (!file) return;
  const fd = new FormData();
  fd.append('csv_file', file);
  setDropLoading(dropId, true);
  try {
    const res  = await fetch('/upload_csv', { method: 'POST', body: fd });
    const data = await res.json();
    console.log('[uploadCsv] Response:', data);  // always log full response
    if (data.success) {
      setDropUploaded(dropId, `✓ ${file.name}`);
      showFileStatus(statusId, `✓ ${data.student_count} students found in ${data.csv_name}`);
      populateStudents(data.students);
      showSection('config-panel');
      showSection('student-panel');
      showToast(`CSV loaded — ${data.student_count} students`, 'success');
    } else {
      setDropError(dropId);
      // Build a descriptive error message
      let msg = data.error || 'Upload failed';
      if (data.columns_found && data.columns_found.length > 0) {
        console.warn('[uploadCsv] Columns in your CSV:', data.columns_found);
        showToast(msg, 'error');
        // Show a second toast with the columns found
        setTimeout(() => {
          showToast(`Columns found: ${data.columns_found.join(' | ')}`, 'info');
        }, 600);
      } else {
        showToast(msg, 'error');
      }
    }
  } catch (e) {
    setDropError(dropId);
    showToast('Upload failed: ' + e.message, 'error');
  }
}

// ── Upload: Syllabus ──────────────────────────────────────
async function uploadSyllabus(file, statusId, dropId) {
  if (!file) return;
  const fd = new FormData();
  fd.append('syllabus_file', file);
  setDropLoading(dropId, true);
  try {
    const res  = await fetch('/upload_syllabus', { method: 'POST', body: fd });
    const data = await res.json();
    if (data.success) {
      setDropUploaded(dropId, `✓ ${file.name}`);
      showFileStatus(statusId, `✓ ${file.name} — ${data.char_count} chars extracted`);
      showToast('Syllabus uploaded & parsed', 'success');
    } else {
      setDropError(dropId);
      showToast(data.error, 'error');
    }
  } catch (e) {
    setDropError(dropId);
    showToast('Upload failed: ' + e.message, 'error');
  }
}

// ── Upload: Question Paper ────────────────────────────────
async function uploadQp(file, statusId, dropId) {
  if (!file) return;
  const fd = new FormData();
  fd.append('qp_file', file);
  setDropLoading(dropId, true);
  try {
    const res  = await fetch('/upload_qp', { method: 'POST', body: fd });
    const data = await res.json();
    if (data.success) {
      setDropUploaded(dropId, `✓ ${file.name}`);
      showFileStatus(statusId, `✓ ${file.name} — ${data.char_count} chars extracted`);
      showToast('Question paper uploaded & parsed', 'success');
    } else {
      setDropError(dropId);
      showToast(data.error, 'error');
    }
  } catch (e) {
    setDropError(dropId);
    showToast('Upload failed: ' + e.message, 'error');
  }
}

// ── Student Grid ──────────────────────────────────────────
function populateStudents(students) {
  state.students = students;
  state.selected = new Set(students); // select all by default
  renderStudentGrid(students);
  updateSelectedCount();
  document.getElementById('student-count-label').textContent =
    `${students.length} student${students.length !== 1 ? 's' : ''} found`;
}

function renderStudentGrid(students) {
  const grid = document.getElementById('student-grid');
  grid.innerHTML = '';
  students.forEach(name => {
    const chip = document.createElement('div');
    chip.className = 'student-chip' + (state.selected.has(name) ? ' selected' : '');
    chip.dataset.name = name;
    chip.innerHTML = `<div class="chip-check">${state.selected.has(name) ? '✓' : ''}</div>
                      <span class="chip-name" title="${name}">${name}</span>`;
    chip.addEventListener('click', () => toggleStudent(name, chip));
    grid.appendChild(chip);
  });
  updateGenerateBtn();
}

function toggleStudent(name, chip) {
  if (state.selected.has(name)) {
    state.selected.delete(name);
    chip.classList.remove('selected');
    chip.querySelector('.chip-check').textContent = '';
  } else {
    state.selected.add(name);
    chip.classList.add('selected');
    chip.querySelector('.chip-check').textContent = '✓';
  }
  updateSelectedCount();
  updateGenerateBtn();
}

function toggleSelectAll(selectAll) {
  state.students.forEach(name => {
    if (selectAll) state.selected.add(name);
    else state.selected.delete(name);
  });
  renderStudentGrid(state.students);
  updateSelectedCount();
  updateGenerateBtn();
}

function filterStudents(query) {
  const q = query.toLowerCase().trim();
  const filtered = state.students.filter(n => n.toLowerCase().includes(q));
  renderStudentGrid(filtered);
}

function updateSelectedCount() {
  const el = document.getElementById('selected-count');
  if (el) el.textContent = `${state.selected.size} selected`;
}

function updateGenerateBtn() {
  const btn = document.getElementById('btn-generate');
  if (btn) btn.disabled = state.selected.size === 0;
}

// ── Generation ────────────────────────────────────────────
async function startGeneration() {
  if (state.selected.size === 0) {
    showToast('Select at least one student.', 'error'); return;
  }

  const testName = document.getElementById('test-name')?.value?.trim() || 'Weekly Test';
  const testDate = document.getElementById('test-date')?.value || '';

  const payload = {
    students: [...state.selected],
    test_name: testName,
    test_date: testDate,
  };

  try {
    const res  = await fetch('/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!data.success) { showToast(data.error, 'error'); return; }

    state.currentJobId = data.job_id;
    showSection('progress-panel');
    hideSection('results-panel');
    scrollTo('progress-panel');
    document.getElementById('btn-generate').disabled = true;
    document.getElementById('btn-generate-text').innerHTML = '<span class="spinner"></span> Generating…';

    listenProgress(data.job_id, state.selected.size);

  } catch (e) {
    showToast('Failed to start: ' + e.message, 'error');
  }
}

function listenProgress(jobId, total) {
  const log   = document.getElementById('progress-log');
  const fill  = document.getElementById('progress-bar-fill');
  const pct   = document.getElementById('progress-pct');
  const meta  = document.getElementById('progress-meta');
  log.innerHTML = '';

  const src = new EventSource(`/stream/${jobId}`);

  src.onmessage = (e) => {
    const msg = JSON.parse(e.data);

    if (msg.type === 'heartbeat') return;

    if (msg.type === 'progress') {
      const p = Math.round((msg.current / total) * 100);
      fill.style.width = p + '%';
      pct.textContent  = p + '%';
      meta.textContent = `Processing ${msg.current} of ${total}: ${msg.name}`;

      const entry = document.createElement('div');
      entry.className = `log-entry ${msg.status === 'Success' ? 'success' : 'failed'}`;
      entry.innerHTML = `<span>${msg.status === 'Success' ? '✓' : '✗'}</span>
                         <span class="log-name">${msg.name}</span>
                         <span class="log-msg">${msg.message}</span>`;
      log.appendChild(entry);
      log.scrollTop = log.scrollHeight;
    }

    if (msg.type === 'done') {
      src.close();
      fill.style.width = '100%';
      pct.textContent  = '100%';
      meta.textContent = 'All done!';
      renderResults(msg.results);

      document.getElementById('btn-generate').disabled = false;
      document.getElementById('btn-generate-text').textContent = 'Generate Reports';
      showToast(`Done! ${msg.results.successful.length} reports generated.`, 'success');
    }

    if (msg.type === 'error') {
      src.close();
      showToast('Stream error: ' + msg.message, 'error');
    }
  };

  src.onerror = () => { src.close(); showToast('Connection lost during generation.', 'error'); };
}

// ── Results Rendering ─────────────────────────────────────
function renderResults(results) {
  showSection('results-panel');
  scrollTo('results-panel');

  const summary = document.getElementById('results-summary');
  summary.textContent = `${results.successful.length} succeeded · ${results.failed.length} failed`;

  state.generatedFiles = results.successful.map(s => s.file_name);

  // Success table
  if (results.successful.length > 0) {
    showSection('success-table-wrap');
    const tbody = document.getElementById('success-tbody');
    tbody.innerHTML = '';
    results.successful.forEach((s, i) => {
      const acc = s.accuracy || 0;
      const accClass = acc >= 70 ? 'high' : acc >= 40 ? 'mid' : 'low';

      // Build action buttons — always show TXT, conditionally show PDF
      let pdfBtns = '';
      if (s.pdf_file_name) {
        pdfBtns = `<a href="/preview/${s.pdf_file_name}" target="_blank" class="btn btn-primary btn-sm">📄 PDF</a>
                   <a href="/download/${s.pdf_file_name}" class="btn btn-ghost btn-sm">⬇️ PDF</a>`;
      }

      const row = document.createElement('tr');
      row.innerHTML = `
        <td style="color:var(--text-muted)">${i + 1}</td>
        <td style="font-weight:600">${s.display_name || s.name}</td>
        <td><span class="marks-chip">${s.total_marks}/300</span></td>
        <td>
          <div class="accuracy-bar-wrap">
            <div class="acc-track"><div class="acc-fill ${accClass}" style="width:${acc}%"></div></div>
            <span class="acc-val">${acc}%</span>
          </div>
        </td>
        <td>
          <div class="action-btns">
            <a href="/preview/${s.file_name}" target="_blank" class="btn btn-ghost btn-sm">👁 TXT</a>
            ${pdfBtns}
            <a href="/download/${s.file_name}" class="btn btn-ghost btn-sm">⬇️ TXT</a>
          </div>
        </td>`;
      tbody.appendChild(row);
    });
  }

  // Failed table
  if (results.failed.length > 0) {
    showSection('failed-table-wrap');
    const tbody = document.getElementById('failed-tbody');
    tbody.innerHTML = '';
    results.failed.forEach(([name, reason], i) => {
      const row = document.createElement('tr');
      row.innerHTML = `<td style="color:var(--text-muted)">${i + 1}</td>
                       <td style="font-weight:600">${name}</td>
                       <td style="color:var(--red);font-size:12px">${reason}</td>`;
      tbody.appendChild(row);
    });
  }
}

// ── Download All ZIP ──────────────────────────────────────
async function downloadAll() {
  if (state.generatedFiles.length === 0) {
    showToast('No files to download.', 'error'); return;
  }
  try {
    const res = await fetch('/download_all', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filenames: state.generatedFiles }),
    });
    if (!res.ok) { showToast('ZIP creation failed.', 'error'); return; }
    const blob = await res.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href = url;
    a.download = `Student_Reports_${Date.now()}.zip`;
    a.click();
    URL.revokeObjectURL(url);
    showToast('ZIP download started!', 'success');
  } catch (e) {
    showToast('Download error: ' + e.message, 'error');
  }
}

// ── Reset Dashboard ────────────────────────────────────────
async function resetDashboard() {
  await fetch('/clear_session', { method: 'POST' });
  location.reload();
}

// ── UI Helpers ────────────────────────────────────────────
function showSection(id) {
  const el = document.getElementById(id);
  if (el) { el.style.display = ''; el.style.animation = 'fade-in 0.35s ease'; }
}
function hideSection(id) {
  const el = document.getElementById(id);
  if (el) el.style.display = 'none';
}
function scrollTo(id) {
  const el = document.getElementById(id);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function setDropLoading(dropId, loading) {
  const inner = document.getElementById(dropId + '-inner');
  if (!inner) return;
  if (loading) inner.innerHTML = '<div class="spinner"></div><p style="color:var(--text-secondary);font-size:13px;margin-top:10px">Uploading…</p>';
}
function setDropUploaded(dropId, label) {
  const zone  = document.getElementById(dropId);
  const inner = document.getElementById(dropId + '-inner');
  if (!zone || !inner) return;
  zone.classList.add('uploaded');
  inner.innerHTML = `<div class="drop-icon">✅</div><p style="color:var(--green);font-size:13px;font-weight:600">${label}</p>`;
}
function setDropError(dropId) {
  const inner = document.getElementById(dropId + '-inner');
  if (inner) inner.innerHTML = `<div class="drop-icon">❌</div><p style="color:var(--red);font-size:13px">Upload failed. Try again.</p>`;
}
function showFileStatus(id, msg) {
  const el = document.getElementById(id);
  if (!el) return;
  el.style.display = 'flex';
  el.textContent = msg;
}

// ── Toast ─────────────────────────────────────────────────
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  const icon = { success: '✅', error: '❌', info: 'ℹ️' }[type] || 'ℹ️';
  toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.classList.add('fade-out');
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}
