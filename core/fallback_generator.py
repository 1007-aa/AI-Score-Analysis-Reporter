"""
Fallback Report Generator — rule-based backup for when Groq AI output
fails validation or the API is unavailable / rate-limited.

Generates structured feedback sections purely from student_data analytics,
guaranteeing a complete PDF report every time.
"""


def generate_fallback_report(student_data, test_name="Weekly Test"):
    """
    Build a complete structured feedback string from raw analytics.
    Output mirrors the exact section headers the parser expects.

    Args:
        student_data: dict from analyzer.analyze_student_data()
        test_name:    name of the assessment

    Returns:
        str: feedback text with all required sections
    """
    name = student_data['student_name']
    total_marks = student_data['total_marks']
    max_marks = student_data['max_marks']
    pct = round(total_marks / max_marks * 100, 1) if max_marks else 0
    accuracy = student_data['accuracy']
    correct = student_data['correct']
    incorrect = student_data['incorrect']
    skipped = student_data['skipped']
    total_q = student_data['total_questions']
    subjects = student_data.get('subjects', {})
    difficulty = student_data.get('difficulty', {})
    time_analysis = student_data.get('time_analysis', {})

    # ── Derive key insights ──────────────────────────────────────
    best_subj = max(subjects, key=lambda s: subjects[s]['marks']) if subjects else None
    worst_subj = min(subjects, key=lambda s: subjects[s]['marks']) if subjects else None
    best_marks = subjects[best_subj]['marks'] if best_subj else 0
    worst_marks = subjects[worst_subj]['marks'] if worst_subj else 0
    best_total = subjects[best_subj]['total'] if best_subj else 1
    worst_total = subjects[worst_subj]['total'] if worst_subj else 1
    best_correct = subjects[best_subj]['correct'] if best_subj else 0
    worst_correct = subjects[worst_subj]['correct'] if worst_subj else 0

    easy_data = difficulty.get('Easy', {})
    easy_correct = easy_data.get('correct', 0)
    easy_total = easy_data.get('total', 1)
    easy_accuracy = round(easy_correct / easy_total * 100, 1) if easy_total else 0

    avg_correct_time = time_analysis.get('Correct', {}).get('avg_time_seconds', 0)
    avg_incorrect_time = time_analysis.get('Incorrect', {}).get('avg_time_seconds', 0)

    # ── Weak topics ──────────────────────────────────────────────
    weak_topics = []
    topic_analysis = student_data.get('topic_analysis')
    if topic_analysis:
        for subj, topics in topic_analysis.items():
            for t in topics:
                if t['total'] > 0:
                    t_acc = t['correct'] / t['total']
                    if t_acc < 0.5:
                        weak_topics.append((subj, t['topic'], t['correct'], t['total']))

    # ── Build sections ───────────────────────────────────────────
    lines = []

    # Strengths
    lines.append("### Strengths Identified")
    lines.append(f"• {name} scored {total_marks}/{max_marks} ({pct}%) with an overall accuracy of {accuracy}%.")
    if best_subj:
        lines.append(f"• Strongest subject is {best_subj} with {best_marks} marks and {best_correct}/{best_total} correct answers.")
    if avg_correct_time > 0:
        lines.append(f"• Average time per correct answer is {avg_correct_time} seconds, showing confident problem-solving on known concepts.")
    if easy_accuracy >= 60:
        lines.append(f"• Good foundation in easy-level questions with {easy_accuracy}% accuracy ({easy_correct}/{easy_total}).")
    else:
        lines.append(f"• Attempted {correct} out of {total_q} questions correctly, demonstrating effort and engagement.")
    lines.append("")

    # Areas Requiring Improvement
    lines.append("### Areas Requiring Improvement")
    if worst_subj and worst_subj != best_subj:
        lines.append(f"• {worst_subj} is the weakest subject with only {worst_marks} marks and {worst_correct}/{worst_total} correct answers — needs focused revision.")
    if easy_accuracy < 60:
        lines.append(f"• Easy-level question accuracy is only {easy_accuracy}%, which should ideally be above 75%. Basic concept strengthening is needed.")
    if avg_incorrect_time > 120:
        lines.append(f"• Spending an average of {avg_incorrect_time} seconds on incorrect answers is too high. Quicker elimination strategies are needed.")
    if skipped > 0:
        lines.append(f"• {skipped} questions were left unanswered. Strategic guessing or better time allocation could recover marks.")
    for subj, topic, t_corr, t_tot in weak_topics[:3]:
        lines.append(f"• In {subj}, the topic \"{topic}\" needs urgent attention — only {t_corr}/{t_tot} correct.")
    lines.append("")

    # Action Plan: Immediate
    lines.append("### Action Plan: Immediate (This Week)")
    if worst_subj:
        lines.append(f"• Dedicate at least 45 minutes daily to revising {worst_subj}, focusing on the weakest topics from this test.")
    lines.append(f"• Review all {incorrect} incorrect answers from {test_name} with detailed solutions and note recurring mistake patterns.")
    lines.append("")

    # Action Plan: Short-Term
    lines.append("### Action Plan: Short-Term (Next 2-3 Weeks)")
    lines.append("• Practice 15-20 timed questions daily across all subjects, with emphasis on weak areas identified above.")
    if weak_topics:
        wt = weak_topics[0]
        lines.append(f"• Complete a focused module on \"{wt[1]}\" in {wt[0]} to build confidence and accuracy.")
    else:
        lines.append(f"• Attempt at least two full-length practice tests under timed conditions to build exam stamina.")
    lines.append("")

    # Action Plan: Long-Term
    lines.append("### Action Plan: Long-Term (Before Next Test)")
    target_pct = min(pct + 15, 90)
    lines.append(f"• Target a score of {target_pct}% or higher in the next test through consistent daily revision.")
    lines.append("• Develop a structured time-management strategy: allocate a fixed time per question and skip quickly if unsure.")
    lines.append("")

    # Message to Parents
    lines.append("### Message to Parents")
    lines.append("Dear Parent,")
    parent_msg = (
        f"We are sharing {name}'s performance report for {test_name}. "
        f"{name} scored {total_marks} out of {max_marks} marks ({pct}%). "
    )
    if best_subj:
        parent_msg += f"{best_subj} was the strongest subject with {best_marks} marks. "
    if worst_subj and worst_subj != best_subj:
        parent_msg += f"However, {worst_subj} requires additional focus, with only {worst_marks} marks. "
    parent_msg += (
        f"We recommend that {name} dedicates consistent daily study time to weak areas, "
        f"particularly revising incorrect answers and practising timed questions. "
        f"With focused effort, we are confident that {name} can show significant improvement in the next assessment."
    )
    lines.append(parent_msg)
    lines.append("")
    lines.append("Warm regards,")
    lines.append("Classes Tutorials — Academic Team")

    return "\n".join(lines)
