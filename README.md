# Classes Score Analysis Automation

AI-powered JEE student performance report generator using **Groq Llama 3.3 70B**.

## Features

- 📊 **Parses** Classes test-export CSVs automatically
- 📖 **Ingests** optional Syllabus & Question Paper (PDF/TXT) for richer AI feedback
- 🤖 **Generates** personalized performance reports via Groq API
- 📁 **Individual `.txt` files** per student — no overwriting
- 🌐 **Web Dashboard** — drag-and-drop uploads, real-time progress, preview & download
- ⚡ **CLI mode** — batch all students or a single student from terminal
- 🔒 `.env`-based credential management (never commit your key)

## Quick Start

### 1. Clone & Setup

```bash
cd score_analysis_automation
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure API Key

```bash
cp .env.example .env
# Edit .env and add your Groq API key:
# GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
```

### 3. Run Web Dashboard

```bash
python main.py --web
# Open http://127.0.0.1:5000
```

### 4. CLI Usage

```bash
# List all students in CSV
python main.py --csv data/scores.csv --list

# Generate report for one student
python main.py --csv data/scores.csv --student "Student"

# Generate reports for ALL students (batch)
python main.py --csv data/scores.csv --all
```

## Project Structure

```
score_analysis_automation/
├── .env                    # Your secrets (never commit)
├── .env.example            # Template
├── config.py               # Environment & path config
├── main.py                 # CLI entry point
├── requirements.txt
│
├── core/
│   ├── analyzer.py         # CSV parsing & metrics
│   ├── report_generator.py # Groq API + report formatter
│   └── batch_processor.py  # Multi-student orchestration
│
├── web/
│   ├── app.py              # Flask web dashboard
│   ├── utils.py            # PDF/TXT text extractor
│   ├── templates/          # Jinja2 HTML templates
│   └── static/             # CSS & JS
│
├── data/                   # Place input CSVs here
└── output/                 # Generated reports saved here
```

## CSV Format

Your CSV must contain these columns:

| Column | Description |
|--------|-------------|
| `Student Name` | Full name |
| `Outcome` | `Correct` / `Incorrect` / `Skipped` |
| `Marks` | Numeric marks for question |
| `Time Taken (in secs)` | Time spent |
| `Subject` | `Physics` / `Chemistry` / `Mathematics` |
| `Difficulty Level` | `Easy` / `Medium` / `Hard` |

Optional columns: `Student ID`, `Roll Number`

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | ✅ Yes | — | Your Groq API key |
| `FLASK_HOST` | No | `127.0.0.1` | Web server host |
| `FLASK_PORT` | No | `5000` | Web server port |
| `FLASK_DEBUG` | No | `True` | Flask debug mode |
