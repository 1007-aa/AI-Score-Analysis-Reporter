import os
import re
from pathlib import Path
from .analyzer import analyze_student_data, get_unique_students
from .report_generator import generate_student_report, create_formatted_report, get_groq_client
from .pdf_generator import generate_student_pdf, _parse_ai_feedback, validate_report_sections
from .fallback_generator import generate_fallback_report
import config


class BatchProcessor:
    def __init__(self, csv_file, output_dir=None):
        self.csv_file = csv_file
        self.output_dir = Path(output_dir) if output_dir else config.OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def sanitize_filename(self, name):
        """Sanitizes student names for safe filesystem filenames."""
        name = name.replace(" ", "_")
        return re.sub(r'(?u)[^\-\w.]', '', name)

    def process_all_students(self, progress_callback=None, syllabus_text=None,
                             qp_text=None, test_name="Weekly Test", test_date=None):
        """Processes all unique students in the CSV file."""
        students = get_unique_students(self.csv_file)
        return self.process_students(
            students, progress_callback=progress_callback,
            syllabus_text=syllabus_text, qp_text=qp_text,
            test_name=test_name, test_date=test_date
        )

    def process_students(self, student_names, progress_callback=None,
                         syllabus_text=None, qp_text=None,
                         test_name="Weekly Test", test_date=None):
        """
        Process a specific list of student names.
        Generates BOTH .txt and .pdf reports for each student.
        progress_callback(current, total, student_name, status, message)
        syllabus_text / qp_text: optional plain text to enrich AI prompts
        """
        results = {
            'successful': [],
            'failed': [],
            'total': len(student_names)
        }

        if not student_names:
            return results

        try:
            client = get_groq_client()
        except Exception as e:
            if progress_callback:
                progress_callback(0, len(student_names), "Initialization", "Failed",
                                  f"API Client init failed: {str(e)}")
            results['failed'] = [
                (name, f"API Key missing or invalid: {str(e)}") for name in student_names
            ]
            return results

        for idx, student_name in enumerate(student_names):
            try:
                # 1. Analyze Data
                student_data = analyze_student_data(student_name, self.csv_file)
                if not student_data:
                    msg = f"No data found for student: {student_name}"
                    if progress_callback:
                        progress_callback(idx + 1, len(student_names), student_name, "Failed", msg)
                    results['failed'].append((student_name, msg))
                    continue

                # 2. Generate AI Feedback
                feedback = None
                used_fallback = False
                try:
                    feedback = generate_student_report(
                        student_data, client=client,
                        syllabus_text=syllabus_text, qp_text=qp_text,
                        test_name=test_name
                    )
                except Exception as ai_err:
                    print(f"  ⚠️  Groq API failed for {student_name}: {ai_err}")

                # 3. Validate AI output — if it fails, use fallback
                if feedback:
                    parsed = _parse_ai_feedback(feedback)
                    is_valid, val_errors = validate_report_sections(parsed, student_name)
                    if not is_valid:
                        print(f"  ⚠️  AI output validation failed for {student_name}: {val_errors}")
                        print(f"      → Auto-repairing with fallback generator...")
                        feedback = generate_fallback_report(student_data, test_name=test_name)
                        used_fallback = True
                else:
                    print(f"  ⚠️  No AI feedback received for {student_name}, using fallback generator.")
                    feedback = generate_fallback_report(student_data, test_name=test_name)
                    used_fallback = True

                # 4. Create full formatted TXT report
                full_report = create_formatted_report(
                    student_data['student_name'], feedback, student_data,
                    test_name=test_name, test_date=test_date
                )

                # 5. Save TXT file
                safe_name = self.sanitize_filename(student_data['student_name'])
                txt_path = self.output_dir / f"Student_Report_{safe_name}.txt"

                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(full_report)

                # 6. Generate PDF file (non-blocking — TXT is always saved first)
                pdf_filename = f"Student_Report_{safe_name}.pdf"
                pdf_path = self.output_dir / pdf_filename
                pdf_ok = False
                try:
                    pdf_ok = generate_student_pdf(
                        student_data, feedback, str(pdf_path),
                        test_name=test_name, test_date=test_date
                    )
                except Exception as pdf_err:
                    print(f"  ⚠️  PDF failed for {student_name}: {pdf_err}")

                if progress_callback:
                    suffix = " (TXT + PDF)" if pdf_ok else " (TXT only)"
                    if used_fallback:
                        suffix += " [fallback]"
                    progress_callback(idx + 1, len(student_names), student_name,
                                      "Success", f"Saved → {txt_path.name}{suffix}")

                results['successful'].append({
                    'name': student_name,
                    'display_name': student_data['student_name'],
                    'file_name': f"Student_Report_{safe_name}.txt",
                    'pdf_file_name': pdf_filename if pdf_ok else None,
                    'path': str(txt_path),
                    'total_marks': student_data['total_marks'],
                    'accuracy': student_data['accuracy'],
                    'feedback_preview': feedback[:300]
                })

            except Exception as e:
                msg = f"Error: {str(e)}"
                if progress_callback:
                    progress_callback(idx + 1, len(student_names), student_name, "Failed", msg)
                results['failed'].append((student_name, msg))

        return results
