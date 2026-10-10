import os
import json
from datetime import datetime
from groq import Groq
import config


def get_groq_client():
    """Helper to initialize Groq client using config key."""
    api_key = config.GROQ_API_KEY or os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is not set. Please add it to your .env file or environment variables."
        )
    return Groq(api_key=api_key)


def generate_student_report(student_data, client=None, syllabus_text=None, qp_text=None, test_name="Weekly Test"):
    """
    Use Groq API to generate a Classes-style feedback report.
    Optionally accepts syllabus and question paper text to enrich the prompt.
    """
    if client is None:
        client = get_groq_client()

    # Build optional context sections
    extra_context = ""
    if syllabus_text:
        extra_context += f"\nSYLLABUS COVERED IN THIS TEST:\n{syllabus_text[:2000]}\n"
    if qp_text:
        extra_context += f"\nQUESTION PAPER TOPICS (first 2000 chars):\n{qp_text[:2000]}\n"

    prompt = f"""You are an expert JEE tutor at Classes creating a personalized student performance report.

STUDENT DATA:
{json.dumps(student_data, indent=2)}
{extra_context}

Generate a detailed performance report following this EXACT format with the specified headers:

### Strengths Identified
• [List 3-4 specific strengths based on data - mention actual numbers/subjects]
• Focus on: fast learning ability, accuracy rate, time management, subject performance
• Be specific: "Good accuracy in Physics (X%)" not just "Good at Physics"

### Areas Requiring Improvement
• [List 3-4 specific areas needing improvement based on performance data]
• Mention specific weak topics from the test (e.g. Mole Concept, Set Operations)
• Highlight negative marks, slow speed on wrong answers, or easy question errors

### Action Plan: Immediate (This Week)
• [List 2 specific actions for this week, e.g. revise mole concept, review incorrect answers]

### Action Plan: Short-Term (Next 2-3 Weeks)
• [List 2 specific actions for the next 2-3 weeks, e.g. practice 20 timed questions daily]

### Action Plan: Long-Term (Before Next Test)
• [List 2 specific actions, e.g. target 60%+ score, improve time management strategy]

### Message to Parents
Dear Parent,
We are sharing {student_data['student_name']}'s performance report for {test_name}.
{student_data['student_name']} scored {student_data['total_marks']} out of {student_data['max_marks']} ({round(student_data['total_marks']/student_data['max_marks']*100, 1)}%).
[Write 2-3 sentences explaining their main strength, their weakest subject that needs focus, and how they can manage their test time better. Ask parents to ensure the student dedicates specific daily revision time to the weak areas.]

Warm regards,
Classes Tutorials — Academic Team

IMPORTANT:
- Write in a professional, encouraging, yet honest tone
- Use bullet points (•) for the Strengths, Improvements, and Action Plans
- Use numbers from the student data to support your insights
- Keep the parent message personal, addressing the parent directly
"""

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are an expert JEE tutor creating personalized student performance feedback reports for Classes.",
            },
            {"role": "user", "content": prompt},
        ],
        model="llama-3.3-70b-versatile",
        temperature=0.7,
        max_tokens=2000,
        top_p=1,
        stream=False,
    )

    return chat_completion.choices[0].message.content


def create_formatted_report(student_name, feedback_text, student_data, test_name="Weekly Test", test_date=None):
    """
    Create a formatted text report with Classes branding.
    test_date defaults to today if not provided.
    """
    if test_date is None:
        test_date = datetime.now().strftime("%d %b %Y")

    generated_on = datetime.now().strftime("%d %b %Y, %I:%M %p")

    report = f"""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║              STUDENT PERFORMANCE ANALYSIS REPORT                 ║
║                    Classes Tutorials                            ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝

════════════════════════════════════════════════════════════════════
STUDENT INFORMATION
════════════════════════════════════════════════════════════════════

Student Name:    {student_name}
Test Name:       {test_name}
Test Date:       {test_date}
Student ID:      {student_data.get('student_id', 'N/A')}
Subjects:        Physics, Chemistry, Mathematics
Mode:            Online

════════════════════════════════════════════════════════════════════
OVERALL PERFORMANCE SUMMARY
════════════════════════════════════════════════════════════════════

Total Marks:           {student_data['total_marks']} / {student_data['max_marks']} ({round(student_data['total_marks']/student_data['max_marks']*100, 1)}%)
Total Questions:       {student_data['total_questions']}
Correct Answers:       {student_data['correct']} ({round(student_data['correct']/student_data['total_questions']*100, 1)}%)
Incorrect Answers:     {student_data['incorrect']} ({round(student_data['incorrect']/student_data['total_questions']*100, 1)}%)
Skipped:              {student_data['skipped']} ({round(student_data['skipped']/student_data['total_questions']*100, 1)}%)
Accuracy:             {student_data['accuracy']}%
Total Time:           {student_data['total_time_minutes']} minutes

════════════════════════════════════════════════════════════════════
SUBJECT-WISE BREAKDOWN
════════════════════════════════════════════════════════════════════
"""

    for subject, data in student_data["subjects"].items():
        accuracy = (
            round((data["correct"] / (data["correct"] + data["incorrect"]) * 100), 1)
            if (data["correct"] + data["incorrect"]) > 0
            else 0
        )
        report += f"""
{subject}:
  Marks:      {data['marks']} / 100 ({data['marks']}%)
  Correct:    {data['correct']} / {data['total']}
  Incorrect:  {data['incorrect']}
  Skipped:    {data['skipped']}
  Accuracy:   {accuracy}%
  Time:       {round(data['time']/60, 1)} min
"""

    report += """
════════════════════════════════════════════════════════════════════
DIFFICULTY-LEVEL ANALYSIS
════════════════════════════════════════════════════════════════════
"""

    for diff, data in student_data["difficulty"].items():
        accuracy = (
            round((data["correct"] / (data["correct"] + data["incorrect"]) * 100), 1)
            if (data["correct"] + data["incorrect"]) > 0
            else 0
        )
        report += f"""
{diff}:  Total: {data['total']} | Correct: {data['correct']} | Wrong: {data['incorrect']} | Skipped: {data['skipped']} | Accuracy: {accuracy}%
"""

    report += f"""
════════════════════════════════════════════════════════════════════
DETAILED FEEDBACK & RECOMMENDATIONS
════════════════════════════════════════════════════════════════════

{feedback_text}

════════════════════════════════════════════════════════════════════

Report Generated: {generated_on}
Confidential - Classes Tutorials Academic Team

For queries, contact your class teacher or email: support@classes.com

════════════════════════════════════════════════════════════════════
"""

    return report
