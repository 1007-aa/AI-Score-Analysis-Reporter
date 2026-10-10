# 🎓 Classes Student Report Generator - Complete Guide

## 📋 What This Does

Generates **professional, Classes-branded PDF reports** using:
- ✅ **Groq API** with `llama-3.3-70b-versatile` for AI-generated feedback
- ✅ **Classes theme**: Blue colors, geometric triangles, professional layout
- ✅ **Comprehensive analysis**: Subject-wise breakdown, strengths, recommendations

---

## 🚀 QUICK START (3 Steps)

### **Step 1: Install Dependencies**

```bash
pip install reportlab groq pandas python-dotenv
```

Or use the requirements file:

```bash
pip install -r requirements.txt
```

### **Step 2: Set Your Groq API Key**

```bash
export GROQ_API_KEY='your-groq-api-key-here'
```

### **Step 3: Run the Generator**

```bash
python3 generate_student_branded_report.py
```

That's it! Your Classes-branded PDF will be in `/mnt/user-data/outputs/`

---

## 📁 Project Structure

```
classes-reports/
├── generate_student_branded_report.py  # Main script (run this)
├── student_pdf_generator.py            # PDF styling & layout
├── report_generator.py                 # Groq API integration
├── requirements.txt                    # Dependencies
├── BPR_SCH_284132__1_.csv             # Student data (input)
└── outputs/
    └── Student_Report_Student.pdf       # Generated report (output)
```

---

## 🎨 What's Included in the PDF

### ✅ Classes Branding Elements:
- **Classes logo** in top-right corner
- **Blue geometric triangles** background (matching your sample)
- **Professional color scheme**: 
  - Primary Blue: #1E88E5
  - Dark Blue: #1565C0
  - Light Blue backgrounds: #E3F2FD

### ✅ Report Sections:
1. **Student Information Table**
   - Name, ID, Test details
   - Professional table formatting

2. **Overall Performance Summary**
   - Total marks, accuracy, time taken
   - Color-coded tables

3. **Subject-Wise Breakdown**
   - Physics, Chemistry, Mathematics
   - Individual metrics for each subject

4. **AI-Generated Feedback** (from Groq API)
   - Strengths
   - Areas for Improvement (per subject)
   - Recommendations
   - All in Classes style!

---

## 🔧 Customization Options

### Change Student Name:

Edit line 118 in `generate_student_branded_report.py`:

```python
STUDENT_NAME = "Student"  # Change to any student name from CSV
```

### Change CSV File:

Edit line 117:

```python
CSV_FILE = "/path/to/your/data.csv"
```

### Modify Classes Colors:

Edit `student_pdf_generator.py`, lines 24-28:

```python
BRAND_BLUE = colors.HexColor('#1E88E5')       # Change primary color
BRAND_DARK_BLUE = colors.HexColor('#1565C0')  # Change dark blue
BRAND_LIGHT_BLUE = colors.HexColor('#E3F2FD') # Change light blue
```

---

## 📊 How It Works

### Flow Diagram:

```
CSV Data → Python Analysis → Groq API (llama-3.3-70b) → Classes PDF
   ↓              ↓                    ↓                      ↓
Students    Calculate Stats    Generate Feedback    Professional PDF
            (marks, accuracy)  (AI insights)        (branded design)
```

### Technical Details:

1. **Data Analysis** (`analyze_student_data()`):
   - Reads CSV with pandas
   - Calculates: total marks, accuracy, subject-wise performance
   - Groups by difficulty level

2. **AI Feedback** (`generate_student_report()`):
   - Calls Groq API with student data
   - Model: `llama-3.3-70b-versatile`
   - Generates: Strengths, Areas for Improvement, Recommendations

3. **PDF Generation** (`generate_student_pdf()`):
   - Uses ReportLab library
   - Applies Classes branding (colors, logo, triangles)
   - Creates professional tables and layouts

---

## 🎯 Output Comparison

### ❌ Your Current Output (Plain Text):
```
Simple .txt file
No branding
No colors
Basic formatting
```

### ✅ New Output (Classes PDF):
```
Professional PDF
Classes logo + branding
Blue color scheme
Geometric triangle background
Professional tables
AI-generated content
```

---

## 🔍 Troubleshooting

### Error: "GROQ_API_KEY not set"
```bash
export GROQ_API_KEY='gsk_your_api_key_here'
```

### Error: "No module named 'reportlab'"
```bash
pip install reportlab --break-system-packages
```

### Error: "Student not found in CSV"
- Check student name spelling
- Make sure CSV file path is correct
- Verify student exists in CSV:
```bash
python3 -c "import pandas as pd; print(pd.read_csv('your_file.csv')['Student Name'].unique())"
```

---

## 🎓 Generate Reports for All Students

Want to generate reports for **all 29 students** at once?

Add this loop to the main script:

```python
# Get all unique student names
df = pd.read_csv(CSV_FILE)
all_students = df['Student Name'].unique()

for student in all_students:
    print(f"\n{'='*70}")
    print(f"Generating report for: {student}")
    print(f"{'='*70}")
    
    # Analyze data
    student_data = analyze_student_data(student, CSV_FILE)
    
    # Generate feedback
    feedback = report_generator.generate_student_report(student_data)
    
    # Create PDF
    output_pdf = f"{OUTPUT_DIR}/Student_Report_{student.replace(' ', '_')}.pdf"
    generate_student_pdf(student_data, feedback, output_pdf)
    
    print(f"✅ Report saved: {output_pdf}")
```

---

## 📈 API Usage (Groq Rate Limits)

For **llama-3.3-70b-versatile**:
- ✅ **30 requests/day** - enough for 29 students
- ✅ **1K tokens/min** - sufficient for report generation
- ✅ **12K tokens/day** - handles multiple reports

**Important**: Generate one report at a time, or space them out to avoid rate limits.

---

## 💡 Additional Improvements You Can Make

### 1. **Add Charts/Graphs**
```python
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart

# Add subject-wise performance chart
```

### 2. **Add Student Photo**
```python
from reportlab.platypus import Image

# Add student photo in header
student_photo = Image('/path/to/photo.jpg', width=1*inch, height=1*inch)
```

### 3. **Multi-language Support**
```python
# Generate reports in Hindi/Regional languages
feedback_hindi = translate_to_hindi(feedback)
```

### 4. **Email Integration**
```python
import smtplib
from email.mime.application import MIMEApplication

# Auto-send PDF to parents via email
```

---

## 📝 Summary

### What You Had Before:
- ✅ Working Groq API integration
- ✅ Good content generation
- ❌ Plain text output
- ❌ No Classes branding

### What You Have Now:
- ✅ Working Groq API integration
- ✅ Good content generation
- ✅ **Professional PDF output**
- ✅ **Full Classes branding**
- ✅ **Geometric triangle design**
- ✅ **Blue color scheme**
- ✅ **Professional tables and layout**

---

## 🎉 You're Done!

Run this command and get your Classes-branded PDF:

```bash
python3 generate_student_branded_report.py
```

The PDF will match the professional design of your sample `12th_JEE_2025_27_Test_Feedback.pdf`!

---

## 📞 Need Help?

Common issues:
1. **Can't install reportlab?** → Use `--break-system-packages` flag
2. **API errors?** → Check your Groq API key is valid
3. **Student not found?** → Verify student name matches CSV exactly

Happy report generating! 🚀
