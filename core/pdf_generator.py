#!/usr/bin/env python3
"""
Classes PDF Report Generator with Professional Branding.
Generates beautiful PDF reports matching Classes's design theme
using ReportLab.

Adapted to fully mirror the design, tables, topic breakdowns, difficulty
analyses, time observations, and parent correspondence styling of the
sample_template.ott document.
"""

import os
import re
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.pdfgen import canvas


# ──────────────────────────────────────────────────────────────
# Classes Brand Tokens
# ──────────────────────────────────────────────────────────────
BRAND_BLUE = colors.HexColor('#1E88E5')
BRAND_DARK_BLUE = colors.HexColor('#1565C0')
BRAND_LIGHT_BLUE = colors.HexColor('#E3F2FD')
BRAND_GRAY = colors.HexColor('#757575')
BRAND_TEXT = colors.HexColor('#212121')


# ──────────────────────────────────────────────────────────────
# Geometric Triangle Background Drawing Helper
# ──────────────────────────────────────────────────────────────
def _draw_triangle_background(c, width, height):
    """Draws the Classes geometric triangle background directly on canvas."""
    # Top-left triangle
    c.saveState()
    c.setFillColorRGB(0.12, 0.53, 0.9, alpha=0.08)
    path = c.beginPath()
    path.moveTo(0, height)
    path.lineTo(120, height)
    path.lineTo(0, height - 120)
    path.close()
    c.drawPath(path, fill=1, stroke=0)
    c.restoreState()

    # Top-right triangle
    c.saveState()
    c.setFillColorRGB(0.08, 0.35, 0.75, alpha=0.12)
    path = c.beginPath()
    path.moveTo(width, height)
    path.lineTo(width - 150, height)
    path.lineTo(width, height - 150)
    path.close()
    c.drawPath(path, fill=1, stroke=0)
    c.restoreState()

    # Bottom-right decorative triangle
    c.saveState()
    c.setFillColorRGB(0.12, 0.53, 0.9, alpha=0.06)
    path = c.beginPath()
    path.moveTo(width, 0)
    path.lineTo(width - 90, 0)
    path.lineTo(width, 90)
    path.close()
    c.drawPath(path, fill=1, stroke=0)
    c.restoreState()


# ──────────────────────────────────────────────────────────────
# Header / Footer
# ──────────────────────────────────────────────────────────────
def _header_footer(canvas_obj, doc):
    """Draw Classes header logo, background, and page footer on every page."""
    canvas_obj.saveState()

    # Draw the background geometric triangles
    _draw_triangle_background(canvas_obj, A4[0], A4[1])

    # Logo drawing: dynamically locate possible logo files in the project root directory
    project_root = Path(__file__).resolve().parent.parent
    possible_paths = [
        project_root / "classes logo-1920-1080.jpg.jpeg",
        project_root / "classes logo-1920-1080.jpeg",
        project_root / "company_logo.png",
        project_root / "company_logo.jpg",
    ]
    
    logo_path = None
    for p in possible_paths:
        if p.exists():
            logo_path = p
            break
            
    logo_width = 44 * mm
    logo_height = 24.75 * mm  # Maintains standard 16:9 ratio
    
    if logo_path:
        # Draw the custom logo centered horizontally at the top of each page
        x = (A4[0] - logo_width) / 2
        y = A4[1] - logo_height - 4 * mm
        canvas_obj.drawImage(str(logo_path), x, y, width=logo_width, height=logo_height, mask='auto')
    else:
        # Fallback: Draw centered Classes brand text
        canvas_obj.setFillColor(BRAND_DARK_BLUE)
        canvas_obj.setFont('Helvetica-Bold', 16)
        canvas_obj.drawCentredString(A4[0] / 2, A4[1] - 18 * mm, "Classes")

    # Footer
    canvas_obj.setFont('Helvetica', 8)
    canvas_obj.setFillColor(BRAND_GRAY)
    canvas_obj.drawCentredString(A4[0] / 2, 15 * mm,
                                  "Classes Tutorials — Student Performance Report")
    canvas_obj.drawRightString(A4[0] - 20 * mm, 15 * mm, f"Page {doc.page}")

    canvas_obj.restoreState()


# ──────────────────────────────────────────────────────────────
# Paragraph Styles
# ──────────────────────────────────────────────────────────────
def _create_styles():
    """Custom paragraph styles matching Classes theme."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='ClassesTitle', parent=styles['Heading1'],
        fontSize=22, textColor=BRAND_DARK_BLUE,
        spaceAfter=15, alignment=TA_CENTER, fontName='Helvetica-Bold'
    ))
    styles.add(ParagraphStyle(
        name='ClassesSubtitle', parent=styles['Normal'],
        fontSize=12, textColor=BRAND_BLUE,
        spaceAfter=20, alignment=TA_CENTER, fontName='Helvetica-Bold'
    ))
    styles.add(ParagraphStyle(
        name='ClassesHeading', parent=styles['Heading2'],
        fontSize=13, textColor=BRAND_DARK_BLUE,
        spaceBefore=14, spaceAfter=8, fontName='Helvetica-Bold',
        borderColor=BRAND_BLUE, borderWidth=1, borderPadding=4, leftIndent=0
    ))
    styles.add(ParagraphStyle(
        name='ClassesSubHeading', parent=styles['Heading3'],
        fontSize=11, textColor=BRAND_BLUE,
        spaceBefore=10, spaceAfter=6, fontName='Helvetica-Bold'
    ))
    styles.add(ParagraphStyle(
        name='ClassesBody', parent=styles['Normal'],
        fontSize=9.5, textColor=BRAND_TEXT,
        alignment=TA_LEFT, spaceAfter=6, leading=13
    ))
    styles.add(ParagraphStyle(
        name='ClassesBullet', parent=styles['Normal'],
        fontSize=9.5, textColor=BRAND_TEXT,
        leftIndent=15, spaceAfter=5, bulletIndent=5, leading=13
    ))
    styles.add(ParagraphStyle(
        name='ParentLetterTitle', parent=styles['Normal'],
        fontSize=11, textColor=BRAND_DARK_BLUE,
        fontName='Helvetica-Bold', spaceAfter=8
    ))
    styles.add(ParagraphStyle(
        name='ParentLetterBody', parent=styles['Normal'],
        fontSize=9, textColor=BRAND_TEXT,
        alignment=TA_JUSTIFY, spaceAfter=8, leading=12.5
    ))
    return styles


# ──────────────────────────────────────────────────────────────
# Table Builders
# ──────────────────────────────────────────────────────────────
def _student_info_table(student_data, test_name="Weekly Test", test_date=None):
    """Student information header table spanning exactly 170mm (A4 printable width)."""
    if test_date is None:
        test_date = datetime.now().strftime("%d %b %Y")

    data = [
        ['Student Name:', student_data['student_name'], 'Test Name:', test_name],
        ['Student ID:', student_data.get('student_id', 'N/A'), 'Test Date:', test_date],
        ['Class:', '12th JEE Preparation', 'Subjects Tested:', 'Physics, Chemistry, Mathematics']
    ]
    # Sum of colWidths = 30 + 55 + 30 + 55 = 170mm
    table = Table(data, colWidths=[30 * mm, 55 * mm, 30 * mm, 55 * mm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), BRAND_LIGHT_BLUE),
        ('BACKGROUND', (2, 0), (2, -1), BRAND_LIGHT_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, -1), BRAND_TEXT),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9.5),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, BRAND_GRAY),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    return table


def _overall_performance_table(student_data):
    """Overall Performance Summary Table matching OTT structure exactly."""
    tq = student_data['total_questions']
    corr = student_data['correct']
    inc = student_data['incorrect']
    sk = student_data['skipped']
    marks = student_data['total_marks']
    max_m = student_data['max_marks']
    pct = round(marks / max_m * 100, 1)

    # Remarks based on percentage
    if pct >= 75:
        remark = "Excellent performance"
    elif pct >= 50:
        remark = "Good; scope for improvement"
    elif pct >= 35:
        remark = "Average; needs revision"
    else:
        remark = "Needs significant improvement"

    # Time remarks
    time_spent = student_data['total_time_minutes']
    time_remark = f"Used {time_spent} min out of 180 min"

    data = [
        ['Metric', 'Score', 'Max', '%', 'Remarks'],
        ['Total Marks', str(marks), str(max_m), f"{pct}%", remark],
        ['Total Questions', str(tq), str(tq), "—", "All questions attempted/seen"],
        ['Correct Answers', str(corr), str(tq), f"{round(corr/tq*100, 1)}%", f"{corr} correct attempts"],
        ['Incorrect Answers', str(inc), str(tq), f"{round(inc/tq*100, 1)}%", "Negative marks deduction risk"],
        ['Skipped / Unattempted', str(sk), str(tq), f"{round(sk/tq*100, 1)}%", "Analyze time management"],
        ['Total Time Spent', f"{time_spent} min", "180 min", "—", time_remark]
    ]

    # Sum of colWidths = 40 + 25 + 25 + 25 + 55 = 170mm
    table = Table(data, colWidths=[40 * mm, 25 * mm, 25 * mm, 25 * mm, 55 * mm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BRAND_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (3, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BRAND_LIGHT_BLUE]),
        ('GRID', (0, 0), (-1, -1), 0.5, BRAND_GRAY),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    return table


def _subject_table(student_data):
    """Subject-wise breakdown table matching OTT structure exactly."""
    data = [['Subject', 'Marks', 'Max', 'Correct', 'Wrong', 'Skipped', 'Score %']]
    for subj_name, s in student_data['subjects'].items():
        score_pct = round(s['marks'] / 100 * 100, 1)
        data.append([
            subj_name,
            str(s['marks']),
            "100",
            str(s['correct']),
            str(s['incorrect']),
            str(s['skipped']),
            f"{score_pct}%"
        ])
    # Sum of colWidths = 40 + 20 + 20 + 20 + 20 + 20 + 30 = 170mm
    table = Table(data, colWidths=[40 * mm, 20 * mm, 20 * mm, 20 * mm, 20 * mm, 20 * mm, 30 * mm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BRAND_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'), # Left-align subject names
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BRAND_LIGHT_BLUE]),
        ('GRID', (0, 0), (-1, -1), 0.5, BRAND_GRAY),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    return table


def _difficulty_table(student_data):
    """Difficulty Analysis Table matching OTT structure exactly."""
    data = [['Difficulty', 'Total Q', 'Correct', 'Wrong', 'Skipped', 'Accuracy']]
    for level, s in student_data['difficulty'].items():
        attempted = s['correct'] + s['incorrect']
        acc = round(s['correct'] / attempted * 100, 1) if attempted > 0 else 0.0
        data.append([
            level,
            str(s['total']),
            str(s['correct']),
            str(s['incorrect']),
            str(s['skipped']),
            f"{acc}%"
        ])
    # Sum of colWidths = 40 + 25 + 25 + 25 + 25 + 30 = 170mm
    table = Table(data, colWidths=[40 * mm, 25 * mm, 25 * mm, 25 * mm, 25 * mm, 30 * mm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BRAND_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'), # Left-align labels
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BRAND_LIGHT_BLUE]),
        ('GRID', (0, 0), (-1, -1), 0.5, BRAND_GRAY),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    return table


def _time_management_table(student_data):
    """Time Management Analysis Table matching OTT structure exactly."""
    data = [['Outcome', 'Avg Time / Question', '# Questions', 'Observation']]
    for outcome, s in student_data['time_analysis'].items():
        data.append([
            outcome,
            f"{s['avg_time_seconds']} sec",
            str(s['count']),
            s['observation']
        ])
    # Sum of colWidths = 35 + 40 + 30 + 65 = 170mm
    table = Table(data, colWidths=[35 * mm, 40 * mm, 30 * mm, 65 * mm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BRAND_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'), # Left-align labels
        ('ALIGN', (3, 1), (3, -1), 'LEFT'), # Left-align observations
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BRAND_LIGHT_BLUE]),
        ('GRID', (0, 0), (-1, -1), 0.5, BRAND_GRAY),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    return table


def _topic_tables(student_data, styles):
    """Topic-wise Breakdown Tables grouped by subject."""
    flowables = []
    if not student_data.get('topic_analysis'):
        return flowables

    for subj_name, topics in student_data['topic_analysis'].items():
        if not topics:
            continue
        flowables.append(Paragraph(f"{subj_name} Topic Performance", styles['ClassesSubHeading']))
        flowables.append(Spacer(1, 1.5 * mm))

        data = [['Topic', 'Q', 'Correct', 'Wrong', 'Marks', 'Skipped']]
        for t in topics:
            data.append([
                t['topic'],
                str(t['total']),
                str(t['correct']),
                str(t['incorrect']),
                f"{t['marks']} / {t['max_marks']}",
                str(t['skipped'])
            ])

        # Sum of colWidths = 60 + 20 + 20 + 20 + 30 + 20 = 170mm
        table = Table(data, colWidths=[60 * mm, 20 * mm, 20 * mm, 20 * mm, 30 * mm, 20 * mm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), BRAND_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'), # Left-align topics
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9.5),
            ('FONTSIZE', (0, 1), (-1, -1), 8.5),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BRAND_LIGHT_BLUE]),
            ('GRID', (0, 0), (-1, -1), 0.5, BRAND_GRAY),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        flowables.append(table)
        flowables.append(Spacer(1, 4 * mm))

    return flowables


# ──────────────────────────────────────────────────────────────
# Parsing Helper
# ──────────────────────────────────────────────────────────────
def _parse_ai_feedback(feedback_text):
    """Parses Groq feedback text into distinct structured sections using length-bounded header checks."""
    sections = {
        'strengths': [],
        'improvements': [],
        'immediate': [],
        'short_term': [],
        'long_term': [],
        'parent_message': ""
    }

    current_section = None
    parent_lines = []

    lines = feedback_text.split('\n')
    for line in lines:
        line_strip = line.strip()
        if not line_strip:
            continue

        lower_line = line_strip.lower()
        clean_header = line_strip.strip('#*:- ').lower()

        # A line is only considered a section header if it is short (less than 50 characters)
        if len(clean_header) < 50:
            if 'strengths identified' in clean_header or 'strengths:' == clean_header or 'strengths' == clean_header:
                current_section = 'strengths'
                continue
            elif 'areas requiring improvement' in clean_header or 'areas for improvement' in clean_header:
                current_section = 'improvements'
                continue
            elif 'immediate' in clean_header:
                current_section = 'immediate'
                continue
            elif 'short-term' in clean_header or 'short term' in clean_header:
                current_section = 'short_term'
                continue
            elif 'long-term' in clean_header or 'long term' in clean_header:
                current_section = 'long_term'
                continue
            elif 'message to parents' in clean_header:
                current_section = 'parent_message'
                continue

        # Check for special 'Dear Parent' initialization line (can be inline or start the paragraph)
        if 'dear parent' in lower_line and len(line_strip) < 30:
            current_section = 'parent_message'
            parent_lines.append(line_strip)
            continue

        # Add line to appropriate section
        if current_section == 'parent_message':
            parent_lines.append(line_strip)
        elif current_section in ['strengths', 'improvements', 'immediate', 'short_term', 'long_term']:
            clean = re.sub(r'^[•\-\*\d\.\s]+', '', line_strip)
            if clean:
                sections[current_section].append(clean)

    sections['parent_message'] = '\n'.join(parent_lines)
    return sections


def validate_report_sections(parsed_data, student_name):
    """
    Validate that all sections are populated, non-empty, and free of placeholders.
    Returns (is_valid, list of error messages)
    """
    errors = []
    
    # 1. Check sections presence
    for field in ['strengths', 'improvements', 'immediate', 'short_term', 'long_term']:
        if not parsed_data.get(field):
            errors.append(f"Section '{field}' is empty or missing.")
            
    if not parsed_data.get('parent_message') or len(parsed_data['parent_message'].strip()) < 50:
        errors.append("Section 'parent_message' is empty, missing, or cut off.")

    # 2. Check for leftover LLM brackets placeholders
    for field, content in parsed_data.items():
        text_to_check = ""
        if isinstance(content, list):
            text_to_check = " ".join(content)
        else:
            text_to_check = content
            
        if '[' in text_to_check or ']' in text_to_check:
            errors.append(f" leftover template brackets detected in section '{field}'")
            
    return len(errors) == 0, errors


# ──────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────
def generate_student_pdf(student_data, feedback_text, output_path,
                         test_name="Weekly Test", test_date=None):
    """
    Generate a professional, Classes-branded PDF report mirroring the
    sample_template.ott template.

    Args:
        student_data: dict from analyzer.analyze_student_data()
        feedback_text: str from report_generator.generate_student_report()
        output_path: str or Path — where to save the PDF
        test_name: str — name of the test
        test_date: str — date string, defaults to today
    """
    output_path = str(output_path)

    try:
        doc = SimpleDocTemplate(
            output_path, pagesize=A4,
            rightMargin=20*mm, leftMargin=20*mm,
            topMargin=25*mm, bottomMargin=25*mm
        )

        story = []
        styles = _create_styles()
        parsed = _parse_ai_feedback(feedback_text)

        # ──────────────────────────────────────────────────────
        # PAGE 1: Quantitative Data & Statistics
        # ──────────────────────────────────────────────────────

        # Title Block
        story.append(Paragraph("STUDENT PERFORMANCE ANALYSIS REPORT", styles['ClassesTitle']))
        story.append(Paragraph(f"{test_name} — Academic Insights", styles['ClassesSubtitle']))
        story.append(Spacer(1, 4 * mm))

        # Student Information
        story.append(Paragraph("Student Information", styles['ClassesHeading']))
        story.append(Spacer(1, 2 * mm))
        story.append(_student_info_table(student_data, test_name, test_date))
        story.append(Spacer(1, 5 * mm))

        # Overall Summary
        story.append(Paragraph("Overall Performance Summary", styles['ClassesHeading']))
        story.append(Spacer(1, 2 * mm))
        story.append(_overall_performance_table(student_data))
        story.append(Spacer(1, 5 * mm))

        # Subject-Wise Breakdown
        story.append(Paragraph("Subject-Wise Breakdown", styles['ClassesHeading']))
        story.append(Spacer(1, 2 * mm))
        story.append(_subject_table(student_data))
        story.append(Spacer(1, 5 * mm))

        # Difficulty Level Analysis
        story.append(Paragraph("Difficulty-Level Analysis", styles['ClassesHeading']))
        story.append(Spacer(1, 2 * mm))
        story.append(_difficulty_table(student_data))

        # Force transition to Page 2
        story.append(PageBreak())

        # ──────────────────────────────────────────────────────
        # PAGE 2: Topics, Time, Strengths/Improvements, Actions, & Parent Box
        # ──────────────────────────────────────────────────────

        # Topic breakdown (if available)
        if student_data.get('topic_analysis'):
            story.append(Paragraph("Topic-Wise Breakdown", styles['ClassesHeading']))
            story.append(Spacer(1, 2 * mm))
            for t_table in _topic_tables(student_data, styles):
                story.append(t_table)
            story.append(Spacer(1, 4 * mm))

        # Time Management Analysis
        story.append(Paragraph("Time Management Analysis", styles['ClassesHeading']))
        story.append(Spacer(1, 2 * mm))
        story.append(_time_management_table(student_data))

        # Print Subject Time Spent underneath
        time_by_subj = " | ".join([f"{subj}: {round(s['time']/60, 1)} min" for subj, s in student_data['subjects'].items()])
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(f"<b>Time Spent by Subject:</b> {time_by_subj}", styles['ClassesBody']))
        story.append(Spacer(1, 4 * mm))

        # Strengths & Weaknesses Stack
        story.append(Paragraph("Strengths Identified", styles['ClassesHeading']))
        story.append(Spacer(1, 1.5 * mm))
        for bullet in parsed['strengths']:
            story.append(Paragraph(f"• {bullet}", styles['ClassesBullet']))
        story.append(Spacer(1, 3 * mm))

        story.append(Paragraph("Areas Requiring Improvement", styles['ClassesHeading']))
        story.append(Spacer(1, 1.5 * mm))
        for bullet in parsed['improvements']:
            story.append(Paragraph(f"• {bullet}", styles['ClassesBullet']))
        
        # Force transition to Page 3 for Action Plan and Message to Parents
        story.append(PageBreak())

        # Recommendations & Action Plan (Three categories)
        story.append(Paragraph("Recommendations &amp; Action Plan", styles['ClassesHeading']))

        # We display Action Plans inside a neat 3-column table
        act_styles = styles
        imm_text = "<br/>".join([f"• {x}" for x in parsed['immediate']]) or "No immediate actions listed."
        st_text = "<br/>".join([f"• {x}" for x in parsed['short_term']]) or "No short-term actions listed."
        lt_text = "<br/>".join([f"• {x}" for x in parsed['long_term']]) or "No long-term actions listed."

        action_data = [
            [
                Paragraph("<b>Immediate (This Week)</b>", act_styles['ClassesSubHeading']),
                Paragraph("<b>Short-Term (Next 2-3 Weeks)</b>", act_styles['ClassesSubHeading']),
                Paragraph("<b>Long-Term (Before Next Test)</b>", act_styles['ClassesSubHeading'])
            ],
            [
                Paragraph(imm_text, act_styles['ClassesBody']),
                Paragraph(st_text, act_styles['ClassesBody']),
                Paragraph(lt_text, act_styles['ClassesBody'])
            ]
        ]
        action_table = Table(action_data, colWidths=[56 * mm, 57 * mm, 57 * mm])
        action_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), BRAND_LIGHT_BLUE),
            ('GRID', (0, 0), (-1, -1), 0.5, BRAND_GRAY),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(action_table)
        story.append(Spacer(1, 5 * mm))

        # Message to Parents styled Box (Callout)
        if parsed['parent_message']:
            parent_paragraphs = []
            for p in parsed['parent_message'].split('\n'):
                p_strip = p.strip()
                if p_strip:
                    parent_paragraphs.append(Paragraph(p_strip, styles['ParentLetterBody']))
            
            # Put them inside a neat layout
            parent_story = [
                Paragraph("Message to Parents", styles['ParentLetterTitle']),
                Spacer(1, 1 * mm)
            ] + parent_paragraphs

            parent_box_table = Table([[parent_story]], colWidths=[170 * mm])
            parent_box_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), BRAND_LIGHT_BLUE),
                ('BOX', (0, 0), (-1, -1), 1, BRAND_BLUE),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ]))
            story.append(parent_box_table)

        # Build with branded header/footer
        doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
        print(f"  ✅ Professional PDF generated: {output_path}")
        return True

    except Exception as e:
        print(f"  ⚠️  PDF generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Classes PDF Generator — import and call generate_student_pdf()")
