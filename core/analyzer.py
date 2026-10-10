import re
import pandas as pd
import numpy as np

REQUIRED_COLUMNS = [
    'Student Name', 
    'Outcome', 
    'Marks', 
    'Time Taken (in secs)', 
    'Subject', 
    'Difficulty Level'
]

# Fuzzy match patterns to map any CSV column naming to our standard REQUIRED_COLUMNS
FUZZY_MAPS = {
    'Student Name': [r'student\s*name', r'^name$', r'candidate\s*name', r'student_name', r'student'],
    'Outcome': [r'^outcome$', r'^result$', r'^status$', r'correctness', r'is\s*correct', r'q\s*status', r'status\s*outcome', r'student\s*outcome'],
    'Marks': [r'^marks$', r'^mark$', r'^score$', r'marks\s*obtained', r'marks_obtained'],
    'Time Taken (in secs)': [r'time\s*taken', r'^time$', r'^duration$', r'seconds', r'secs', r'time_taken'],
    # 'Subject Name' in Classes exports → mapped to 'Subject'
    'Subject': [r'subject\s*name', r'^subject\b', r'^subject$', r'^course$'],
    # 'Difficulty' (no 'Level' suffix) in Classes exports → mapped to 'Difficulty Level'
    'Difficulty Level': [r'difficulty\s*level', r'^difficulty$', r'^difficulty\b', r'^level$', r'^diff$'],
    # Optional columns for detailed topic mapping
    'Chapter Name': [r'chapter\s*name', r'^chapter$', r'chapter_name'],
    'Topic Name': [r'topic\s*name', r'^topic$', r'topic_name']
}

def normalize_df(df):
    """
    Fuzzy maps and standardizes CSV column names to the expected format.
    Returns (normalized_df, missing_cols)
    """
    df = df.copy()
    cols = list(df.columns)
    mapped = {}
    
    for req, patterns in FUZZY_MAPS.items():
        found = False
        # 1. Try exact match (case insensitive)
        for col in cols:
            if col.strip().lower() == req.lower():
                mapped[col] = req
                found = True
                break
        
        # 2. Try fuzzy patterns if exact not found
        if not found:
            for pattern in patterns:
                for col in cols:
                    if re.search(pattern, col.strip().lower()):
                        mapped[col] = req
                        found = True
                        break
                if found:
                    break
                    
    # Rename matching columns
    df = df.rename(columns=mapped)
    
    # Standardize student name strings
    if 'Student Name' in df.columns:
        df['Student Name'] = df['Student Name'].astype(str).str.strip()
        
    # Standardize subject strings
    if 'Subject' in df.columns:
        df['Subject'] = df['Subject'].astype(str).str.strip()
        
    # Standardize Outcome values
    if 'Outcome' in df.columns:
        df['Outcome'] = df['Outcome'].astype(str).str.strip().str.upper()
        outcome_map = {
            'CORRECT': 'Correct',
            'INCORRECT': 'Incorrect',
            'NOT_ANSWERED': 'Skipped',
            'SKIPPED': 'Skipped',
            'UNATTEMPTED': 'Skipped',
            'CORRECT_ANSWER': 'Correct',
            'WRONG_ANSWER': 'Incorrect',
            'WRONG': 'Incorrect'
        }
        df['Outcome'] = df['Outcome'].map(outcome_map).fillna(df['Outcome'].str.title())
        
    # Standardize Difficulty Level values
    if 'Difficulty Level' in df.columns:
        df['Difficulty Level'] = df['Difficulty Level'].astype(str).str.strip().str.upper()
        diff_map = {
            'EASY': 'Easy',
            'MEDIUM': 'Medium',
            'HARD': 'Hard'
        }
        df['Difficulty Level'] = df['Difficulty Level'].map(diff_map).fillna(df['Difficulty Level'].str.title())
        
    # Identify what's missing (only check required ones, not the optional Chapter/Topic Name)
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    return df, missing

def validate_csv(csv_file):
    """
    Validate that the CSV has the required columns and is readable.
    Returns (is_valid, error_message)
    """
    try:
        df = pd.read_csv(csv_file, nrows=5)
        _, missing = normalize_df(df)
        if missing:
            return False, f"Missing required columns: {', '.join(missing)}"
        return True, ""
    except Exception as e:
        return False, f"Could not read CSV file: {str(e)}"

def get_unique_students(csv_file):
    """
    Returns a sorted list of unique student names from the CSV file.
    """
    try:
        df = pd.read_csv(csv_file)
        df, missing = normalize_df(df)
        if 'Student Name' not in df.columns:
            return []
        return sorted(df['Student Name'].dropna().unique().tolist())
    except Exception:
        return []

def analyze_student_data(student_name, csv_file):
    """
    Analyze student performance from CSV data
    """
    try:
        raw_df = pd.read_csv(csv_file)
        df, missing = normalize_df(raw_df)
        if missing:
            print(f"Error: missing required columns: {missing}")
            return None
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return None
        
    student_df = df[df['Student Name'].str.strip().str.lower() == student_name.strip().lower()]
    
    if student_df.empty:
        return None
        
    # Get official name casing from the data
    actual_name = student_df['Student Name'].iloc[0]
    
    # Calculate metrics
    total_questions = len(student_df)
    correct = len(student_df[student_df['Outcome'] == 'Correct'])
    incorrect = len(student_df[student_df['Outcome'] == 'Incorrect'])
    skipped = len(student_df[student_df['Outcome'] == 'Skipped'])
    total_marks = student_df['Marks'].sum()
    total_time = student_df['Time Taken (in secs)'].sum()
    
    # Try to fetch Student ID if available in dataset
    student_id = "N/A"
    if 'Student ID' in student_df.columns:
        student_id = str(student_df['Student ID'].iloc[0])
    elif 'Roll Number' in student_df.columns:
        student_id = str(student_df['Roll Number'].iloc[0])
    
    # Subject-wise analysis (dynamically identify or fallback to standard ones)
    subjects = {}
    found_subjects = student_df['Subject'].dropna().unique()
    if len(found_subjects) == 0:
        found_subjects = ['Physics', 'Chemistry', 'Mathematics']
        
    for subject in found_subjects:
        subj_df = student_df[student_df['Subject'] == subject]
        subjects[subject] = {
            'total': len(subj_df),
            'correct': len(subj_df[subj_df['Outcome'] == 'Correct']),
            'incorrect': len(subj_df[subj_df['Outcome'] == 'Incorrect']),
            'skipped': len(subj_df[subj_df['Outcome'] == 'Skipped']),
            'marks': int(subj_df['Marks'].sum()),
            'time': float(subj_df['Time Taken (in secs)'].sum())
        }
    
    # Difficulty-wise analysis
    difficulty_levels = {}
    found_difficulties = student_df['Difficulty Level'].dropna().unique()
    # Sort order: Easy, Medium, Hard
    diff_order = {'Easy': 1, 'Medium': 2, 'Hard': 3}
    found_difficulties = sorted(found_difficulties, key=lambda x: diff_order.get(x, 99))
    if len(found_difficulties) == 0:
        found_difficulties = ['Easy', 'Medium', 'Hard']
        
    for diff in found_difficulties:
        diff_df = student_df[student_df['Difficulty Level'] == diff]
        difficulty_levels[diff] = {
            'total': len(diff_df),
            'correct': len(diff_df[diff_df['Outcome'] == 'Correct']),
            'incorrect': len(diff_df[diff_df['Outcome'] == 'Incorrect']),
            'skipped': len(diff_df[diff_df['Outcome'] == 'Skipped'])
        }

    # Topic-wise analysis: group by Subject and then by Chapter/Topic Name
    topic_analysis = {}
    topic_col = None
    if 'Topic Name' in student_df.columns:
        topic_col = 'Topic Name'
    elif 'Chapter Name' in student_df.columns:
        topic_col = 'Chapter Name'

    if topic_col:
        for subj in found_subjects:
            subj_df = student_df[student_df['Subject'] == subj]
            topic_analysis[subj] = []
            
            unique_topics = subj_df[topic_col].dropna().unique()
            for topic in unique_topics:
                t_df = subj_df[subj_df[topic_col] == topic]
                t_total = len(t_df)
                t_correct = len(t_df[t_df['Outcome'] == 'Correct'])
                t_incorrect = len(t_df[t_df['Outcome'] == 'Incorrect'])
                t_skipped = len(t_df[t_df['Outcome'] == 'Skipped'])
                t_marks = int(t_df['Marks'].sum())
                t_max = t_total * 4 # Standard JEE 4 marks per question
                
                topic_analysis[subj].append({
                    'topic': str(topic),
                    'total': int(t_total),
                    'correct': int(t_correct),
                    'incorrect': int(t_incorrect),
                    'skipped': int(t_skipped),
                    'marks': int(t_marks),
                    'max_marks': int(t_max)
                })
    else:
        topic_analysis = None

    # Time management analysis: calculate avg time and count per outcome
    time_analysis = {}
    for outcome in ['Correct', 'Incorrect', 'Skipped']:
        o_df = student_df[student_df['Outcome'] == outcome]
        o_count = len(o_df)
        if o_count > 0:
            avg_time = float(o_df['Time Taken (in secs)'].mean())
        else:
            avg_time = 0.0
            
        observation = ""
        if outcome == 'Correct':
            if avg_time < 90:
                observation = "Quick & accurate on known concepts"
            else:
                observation = "Accurate but slow; needs speed drills"
        elif outcome == 'Incorrect':
            if avg_time > 120:
                observation = "Spends too long on incorrect attempts"
            else:
                observation = "Careless errors or guessing; review theory"
        elif outcome == 'Skipped':
            if avg_time > 90:
                observation = "Wasted time before skipping; skip faster"
            else:
                observation = "Good exam strategy; skipped quickly"
                
        time_analysis[outcome] = {
            'count': int(o_count),
            'avg_time_seconds': round(avg_time, 1),
            'observation': observation
        }
    
    return {
        'student_name': actual_name,
        'student_id': student_id,
        'total_questions': int(total_questions),
        'correct': int(correct),
        'incorrect': int(incorrect),
        'skipped': int(skipped),
        'total_marks': int(total_marks),
        'max_marks': 300,
        'total_time_minutes': round(float(total_time) / 60, 1),
        'accuracy': round((correct / (correct + incorrect) * 100), 1) if (correct + incorrect) > 0 else 0,
        'subjects': subjects,
        'difficulty': difficulty_levels,
        'topic_analysis': topic_analysis,
        'time_analysis': time_analysis
    }
