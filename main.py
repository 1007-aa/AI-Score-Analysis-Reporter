#!/usr/bin/env python3
import sys
import argparse
import os
from pathlib import Path

# Add root folder to python path to avoid package resolution issues
sys.path.insert(0, str(Path(__file__).resolve().parent))

import config
from core import (
    validate_csv, 
    get_unique_students, 
    analyze_student_data, 
    generate_student_report, 
    create_formatted_report,
    BatchProcessor
)

# Rich prints and progress visualization
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.theme import Theme

custom_theme = Theme({
    "info": "dim cyan",
    "warning": "magenta",
    "danger": "bold red",
    "success": "bold green",
})
console = Console(theme=custom_theme)

def display_welcome():
    welcome_text = """
 [bold cyan]🚀 Classes Performance Report Generator[/bold cyan]
 [dim]Enterprise AI-driven Student Insights & Recommendations[/dim]
    """
    console.print(Panel(welcome_text, border_style="cyan"))

def list_students(csv_path):
    with console.status("[bold yellow]Scanning CSV for students...", spinner="dots"):
        is_valid, err = validate_csv(csv_path)
        if not is_valid:
            console.print(f"[bold red]❌ Invalid CSV File:[/bold red] {err}")
            return
        
        students = get_unique_students(csv_path)
        
    if not students:
        console.print("[yellow]⚠️ No student records found in CSV.[/yellow]")
        return
        
    table = Table(title=f"Students in {Path(csv_path).name}", header_style="bold magenta")
    table.add_column("No.", justify="right", style="cyan")
    table.add_column("Student Name", style="white")
    
    for idx, name in enumerate(students, 1):
        table.add_row(str(idx), name)
        
    console.print(table)
    console.print(f"\n[green]Total Students found: [bold]{len(students)}[/bold][/green]")

def process_single(csv_path, student_name):
    is_valid, err = validate_csv(csv_path)
    if not is_valid:
        console.print(f"[bold red]❌ Invalid CSV File:[/bold red] {err}")
        return
        
    console.print(f"\n[bold yellow]Step 1: Analyzing metrics for {student_name}...[/bold yellow]")
    student_data = analyze_student_data(student_name, csv_path)
    if not student_data:
        console.print(f"[bold red]❌ Error:[/bold red] Student '[bold]{student_name}[/bold]' not found in CSV.")
        return
        
    console.print(f"[bold green]✓[/bold green] Student metrics calculated successfully:")
    console.print(f"  - Questions: {student_data['total_questions']} | Accuracy: {student_data['accuracy']}%")
    console.print(f"  - Marks: {student_data['total_marks']}/{student_data['max_marks']}")
    
    console.print(f"\n[bold yellow]Step 2: Sending data to Groq (Llama-3.3-70b-versatile)...[/bold yellow]")
    try:
        feedback = generate_student_report(student_data)
        console.print(f"[bold green]✓[/bold green] AI Personalized Feedback generated successfully!")
    except Exception as e:
        console.print(f"[bold red]❌ Groq API Call Failed:[/bold red] {str(e)}")
        console.print("[dim yellow]Ensure GROQ_API_KEY is configured in your .env file.[/dim yellow]")
        return
        
    console.print(f"\n[bold yellow]Step 3: Compiling branded PDF/Text Report...[/bold yellow]")
    full_report = create_formatted_report(student_data['student_name'], feedback, student_data)
    
    safe_name = student_data['student_name'].replace(" ", "_")
    output_file = config.OUTPUT_DIR / f"Student_Report_{safe_name}.txt"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(full_report)
        
    console.print(f"[bold success]✓ Success![/bold success] Saved to [bold cyan]{output_file.resolve()}[/bold cyan]")
    
    # Preview feedback first 300 chars
    console.print(Panel(feedback[:400] + "...", title="Feedback Snippet Preview", border_style="green"))

def process_batch(csv_path):
    is_valid, err = validate_csv(csv_path)
    if not is_valid:
        console.print(f"[bold red]❌ Invalid CSV File:[/bold red] {err}")
        return
        
    students = get_unique_students(csv_path)
    if not students:
        console.print("[yellow]⚠️ No student records to process.[/yellow]")
        return
        
    console.print(f"\n[bold yellow]Batch Processing {len(students)} Student Reports...[/bold yellow]")
    processor = BatchProcessor(csv_path)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Processing reports...", total=len(students))
        
        def update_progress(current, total, name, status, msg):
            progress.update(task, completed=current, description=f"[cyan]Current: [bold]{name}[/bold] ({status})")
            if status == "Success":
                console.print(f"  [green]✓[/green] [bold]{name}[/bold]: {msg}")
            else:
                console.print(f"  [red]✗[/red] [bold]{name}[/bold]: {msg}")

        results = processor.process_students(students, progress_callback=update_progress)
        
    console.print("\n[bold success]🎉 Batch Processing Finished![/bold success]")
    console.print(f"  - Generated: [green]{len(results['successful'])}[/green]")
    console.print(f"  - Failed: [red]{len(results['failed'])}[/red]")

def launch_web_server():
    console.print("[bold yellow]Launching local Flask Web Dashboard...[/bold yellow]")
    # Import inside function to delay web dashboard imports unless explicitly running web
    try:
        from web.app import app
        console.print(f"[green]Dashboard runs locally on: [bold]http://{config.FLASK_HOST}:{config.FLASK_PORT}[/bold][/green]")
        app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=config.FLASK_DEBUG)
    except Exception as e:
        console.print(f"[bold red]Failed to start Flask app:[/bold red] {e}")

def main():
    parser = argparse.ArgumentParser(description="Classes Student Performance Report Generator")
    parser.add_argument("--csv", help="Path to raw scores export CSV file", default=None)
    parser.add_argument("--student", help="Student Name to generate report for", default=None)
    parser.add_argument("--all", action="store_true", help="Generate reports for ALL students in the CSV")
    parser.add_argument("--list", action="store_true", help="List all unique students in the CSV")
    parser.add_argument("--web", action="store_true", help="Start Web Dashboard")
    
    args = parser.parse_args()
    
    display_welcome()
    
    # 1. Validate environment configuration
    ok, errors = config.validate_config()
    if not ok and not args.list:
        console.print("[bold red]❌ Environment Validation Failed:[/bold red]")
        for err in errors:
            console.print(f"  - {err}")
        console.print("\n[dim yellow]Please create a '.env' file in this folder and add your GROQ_API_KEY.[/dim yellow]")
        if not args.web:
            sys.exit(1)
            
    # 2. Determine target CSV
    csv_path = args.csv
    if not csv_path and not args.web:
        # Check standard default folders
        if Path("data/scores.csv").exists():
            csv_path = "data/scores.csv"
        elif Path("/mnt/user-data/uploads/BPR_SCH_284132__1_.csv").exists():
            csv_path = "/mnt/user-data/uploads/BPR_SCH_284132__1_.csv"
        else:
            console.print("[bold red]❌ Error:[/bold red] No CSV path specified. Use --csv <path>")
            sys.exit(1)
            
    # 3. Routes command actions
    if args.web:
        launch_web_server()
    elif args.list:
        list_students(csv_path)
    elif args.all:
        process_batch(csv_path)
    elif args.student:
        process_single(csv_path, args.student)
    else:
        # Default behavior: Show usage or prompt to launch web mode
        parser.print_help()
        console.print("\n[cyan]Tip: Run with --web to get a graphical browser interface![/cyan]")

if __name__ == "__main__":
    main()
