"""
Flask Web Dashboard for Classes Report Generator.
Supports: CSV upload, Syllabus upload, Question Paper upload,
          real-time SSE progress, individual & ZIP downloads.
"""
import sys
import os
import json
import queue
import threading
import zipfile
import io
from pathlib import Path
from datetime import datetime

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import (
    Flask, render_template, request, redirect, url_for,
    jsonify, send_file, Response, session, flash
)
from werkzeug.utils import secure_filename

import config
from core import validate_csv, get_unique_students, analyze_student_data
from core.batch_processor import BatchProcessor
from web.utils import extract_text_from_file

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "classes-dev-secret-2026")

ALLOWED_CSV = {'csv'}
ALLOWED_DOCS = {'pdf', 'txt', 'md'}

# In-memory store keyed by session job_id
_job_queues: dict[str, queue.Queue] = {}
_job_results: dict[str, dict] = {}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def allowed_file(filename, allowed_set):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_set


def save_upload(file, subdir, allowed_set):
    """Save an uploaded file; returns (saved_path, error_message)."""
    if not file or file.filename == '':
        return None, "No file selected."
    if not allowed_file(file.filename, allowed_set):
        return None, f"File type not allowed. Allowed: {', '.join(allowed_set)}"
    filename = secure_filename(file.filename)
    dest_dir = config.UPLOADS_DIR / subdir
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / filename
    file.save(str(dest_path))
    return str(dest_path), None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')


@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    """Upload the student scores CSV and return the student list."""
    file = request.files.get('csv_file')

    # ── Debug: log what file was received ──────────────────────────────
    print(f"\n[UPLOAD_CSV] Received file: {file.filename if file else 'None'}")

    path, err = save_upload(file, 'csv', ALLOWED_CSV)
    if err:
        print(f"[UPLOAD_CSV] Save failed: {err}")
        return jsonify({'success': False, 'error': err}), 400

    # ── Debug: print what columns the CSV actually has ─────────────────
    try:
        import pandas as pd
        df_peek = pd.read_csv(path, nrows=2)
        actual_cols = list(df_peek.columns)
        print(f"[UPLOAD_CSV] Columns found in CSV: {actual_cols}")
    except Exception as peek_err:
        print(f"[UPLOAD_CSV] Could not peek at CSV columns: {peek_err}")
        actual_cols = []

    is_valid, validation_err = validate_csv(path)
    if not is_valid:
        print(f"[UPLOAD_CSV] Validation failed: {validation_err}")
        print(f"[UPLOAD_CSV] Columns in file: {actual_cols}")
        os.remove(path)
        return jsonify({
            'success': False,
            'error': f'{validation_err}',
            'columns_found': actual_cols,
            'hint': 'Check the terminal/console for the list of columns found in your CSV.'
        }), 400

    students = get_unique_students(path)
    session['csv_path'] = path
    session['csv_name'] = file.filename
    print(f"[UPLOAD_CSV] Success — {len(students)} students loaded.")

    return jsonify({
        'success': True,
        'students': students,
        'student_count': len(students),
        'csv_name': file.filename
    })


@app.route('/diagnose_csv', methods=['POST'])
def diagnose_csv():
    """
    Debug endpoint: upload a CSV and get back its raw column names.
    Useful for diagnosing upload failures without changing any state.
    """
    file = request.files.get('csv_file')
    if not file or file.filename == '':
        return jsonify({'success': False, 'error': 'No file received'}), 400

    try:
        import pandas as pd
        df = pd.read_csv(file, nrows=3)
        cols = list(df.columns)
        sample = df.head(2).to_dict(orient='records')
        print(f"[DIAGNOSE_CSV] Columns: {cols}")
        return jsonify({'success': True, 'columns': cols, 'sample_rows': sample})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/upload_syllabus', methods=['POST'])
def upload_syllabus():
    """Upload syllabus PDF/TXT and store path in session."""
    file = request.files.get('syllabus_file')
    path, err = save_upload(file, 'syllabus', ALLOWED_DOCS)
    if err:
        return jsonify({'success': False, 'error': err}), 400

    text = extract_text_from_file(path, file.filename)
    session['syllabus_path'] = path
    session['syllabus_name'] = file.filename

    return jsonify({
        'success': True,
        'file_name': file.filename,
        'preview': text[:300] + ('...' if len(text) > 300 else ''),
        'char_count': len(text)
    })


@app.route('/upload_qp', methods=['POST'])
def upload_qp():
    """Upload question paper PDF/TXT and store path in session."""
    file = request.files.get('qp_file')
    path, err = save_upload(file, 'qp', ALLOWED_DOCS)
    if err:
        return jsonify({'success': False, 'error': err}), 400

    text = extract_text_from_file(path, file.filename)
    session['qp_path'] = path
    session['qp_name'] = file.filename

    return jsonify({
        'success': True,
        'file_name': file.filename,
        'preview': text[:300] + ('...' if len(text) > 300 else ''),
        'char_count': len(text)
    })


@app.route('/generate', methods=['POST'])
def generate():
    """Start batch report generation job. Returns a job_id for SSE polling."""
    data = request.get_json()

    csv_path = session.get('csv_path')
    if not csv_path or not Path(csv_path).exists():
        return jsonify({'success': False, 'error': 'No CSV uploaded. Please upload a CSV first.'}), 400

    selected_students = data.get('students', [])
    if not selected_students:
        return jsonify({'success': False, 'error': 'No students selected.'}), 400

    test_name = data.get('test_name', 'Weekly Test').strip() or 'Weekly Test'
    test_date = data.get('test_date', '').strip() or None

    # Extract supplemental context
    syllabus_text = None
    qp_text = None
    syllabus_path = session.get('syllabus_path')
    qp_path = session.get('qp_path')
    syllabus_name = session.get('syllabus_name', '')
    qp_name = session.get('qp_name', '')

    if syllabus_path and Path(syllabus_path).exists():
        syllabus_text = extract_text_from_file(syllabus_path, syllabus_name)
    if qp_path and Path(qp_path).exists():
        qp_text = extract_text_from_file(qp_path, qp_name)

    # Create a unique job ID
    job_id = datetime.now().strftime('%Y%m%d%H%M%S%f')
    q = queue.Queue()
    _job_queues[job_id] = q
    _job_results[job_id] = {}

    def run_batch():
        processor = BatchProcessor(csv_path)

        def progress_cb(current, total, name, status, msg):
            q.put({
                'type': 'progress',
                'current': current,
                'total': total,
                'name': name,
                'status': status,
                'message': msg
            })

        results = processor.process_students(
            selected_students,
            progress_callback=progress_cb,
            syllabus_text=syllabus_text,
            qp_text=qp_text,
            test_name=test_name,
            test_date=test_date
        )
        _job_results[job_id] = results
        q.put({'type': 'done', 'results': results})

    t = threading.Thread(target=run_batch, daemon=True)
    t.start()

    return jsonify({'success': True, 'job_id': job_id})


@app.route('/stream/<job_id>')
def stream(job_id):
    """SSE endpoint — streams progress events for a given job."""
    def event_stream():
        q = _job_queues.get(job_id)
        if not q:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Invalid job ID'})}\n\n"
            return

        while True:
            try:
                msg = q.get(timeout=120)
                yield f"data: {json.dumps(msg)}\n\n"
                if msg.get('type') == 'done':
                    break
            except queue.Empty:
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"

    return Response(event_stream(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


@app.route('/results/<job_id>')
def results(job_id):
    """Returns final JSON results for a completed job."""
    res = _job_results.get(job_id)
    if res is None:
        return jsonify({'success': False, 'error': 'Job not found or still running'}), 404
    return jsonify({'success': True, 'results': res})


@app.route('/preview/<path:filename>')
def preview(filename):
    """Render a generated report. TXT renders in HTML; PDF served inline."""
    report_path = config.OUTPUT_DIR / filename
    if not report_path.exists():
        return "Report not found.", 404

    # PDF → serve inline so the browser renders it natively
    if filename.lower().endswith('.pdf'):
        return send_file(str(report_path), mimetype='application/pdf',
                         as_attachment=False, download_name=filename)

    # TXT → render inside report.html template
    content = report_path.read_text(encoding='utf-8')
    return render_template('report.html', filename=filename, content=content)


@app.route('/download/<path:filename>')
def download(filename):
    """Download a single generated report."""
    report_path = config.OUTPUT_DIR / filename
    if not report_path.exists():
        return "File not found.", 404
    return send_file(str(report_path), as_attachment=True, download_name=filename)


@app.route('/download_all', methods=['POST'])
def download_all():
    """ZIP up all files listed in request JSON, prioritizing PDFs over TXTs."""
    data = request.get_json()
    filenames = data.get('filenames', [])

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fname in filenames:
            fpath = config.OUTPUT_DIR / fname
            # If we are requested a .txt file, check if a matching .pdf exists
            if fname.endswith('.txt'):
                pdf_fname = fname.replace('.txt', '.pdf')
                pdf_path = config.OUTPUT_DIR / pdf_fname
                if pdf_path.exists():
                    # PDF exists -> add ONLY the PDF to the ZIP
                    zf.write(str(pdf_path), arcname=pdf_fname)
                elif fpath.exists():
                    # PDF missing -> fall back to the TXT file
                    zf.write(str(fpath), arcname=fname)
            else:
                # For non-txt files or explicit requests, add directly
                if fpath.exists():
                    zf.write(str(fpath), arcname=fname)
    zip_buffer.seek(0)

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    return send_file(
        zip_buffer,
        as_attachment=True,
        download_name=f'Student_Reports_{ts}.zip',
        mimetype='application/zip'
    )


@app.route('/clear_session', methods=['POST'])
def clear_session():
    """Reset uploads stored in session."""
    for key in ['csv_path', 'csv_name', 'syllabus_path', 'syllabus_name', 'qp_path', 'qp_name']:
        session.pop(key, None)
    return jsonify({'success': True})


@app.route('/health')
def health():
    ok, errors = config.validate_config()
    return jsonify({
        'status': 'ok' if ok else 'degraded',
        'groq_key_set': bool(config.GROQ_API_KEY),
        'errors': errors
    })


if __name__ == '__main__':
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=config.FLASK_DEBUG)
