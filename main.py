# =============================================================================
# main.py — Orchestrator: startup, menu, analysis flow, result display
# Smart Battery Reuse Identification System
# =============================================================================

import sys

from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.table import Table
from rich import box

from utils import (
    console,
    clear_screen,
    show_banner,
    show_separator,
    simulate_progress,
)
from image_processing import preprocess_image, detect_defects
from classifier import classify_battery
from report_generator import generate_report


# ─── Input collection ─────────────────────────────────────────────────────────

def get_battery_input():
    """Prompt the user for battery details and return validated values."""
    console.print()
    console.print(Rule(" [bold cyan]BATTERY INPUT[/bold cyan] ", style="cyan"))
    console.print()

    image_path = Prompt.ask("  [white]Image path      [/white]", default="battery.jpg")
    battery_id = Prompt.ask("  [white]Battery ID      [/white]", default="BAT-001")

    while True:
        raw = Prompt.ask("  [white]Voltage (V)     [/white]", default="3.7")
        try:
            voltage = float(raw)
            if 0.0 <= voltage <= 5.0:
                break
            console.print("  [yellow]  Enter a value between 0.0 and 5.0 V.[/yellow]")
        except ValueError:
            console.print("  [red]  Invalid input — enter a numeric value.[/red]")

    return image_path, battery_id, voltage


# ─── Result display ───────────────────────────────────────────────────────────

def display_results(
    battery_id, voltage, prep_steps, defects, grade, recommendation
):
    """Render analysis results in structured rich panels."""
    console.print()

    # ── Preprocessing panel ───────────────────────────────────────────────────
    lines = []
    for step in prep_steps:
        if "simulated" in step.lower():
            lines.append(f"  [yellow]⚠[/yellow]  {step}")
        else:
            lines.append(f"  [green]✓[/green]  {step}")

    console.print(Panel(
        "\n".join(lines),
        title="[bold cyan] IMAGE PREPROCESSING [/bold cyan]",
        border_style="cyan",
        padding=(0, 1),
    ))

    console.print()

    # ── Defect analysis table ─────────────────────────────────────────────────
    dt = Table(
        box=box.SIMPLE_HEAVY,
        show_header=True,
        header_style="bold white on #0f3460",
        padding=(0, 2),
        expand=False,
    )
    dt.add_column("Defect Type",  style="white",    width=18)
    dt.add_column("Status",       justify="center", width=14)
    dt.add_column("Severity",     justify="center", width=14)
    dt.add_column("Confidence",   justify="center", width=14)

    for d in defects:
        if d["detected"]:
            status_str = "[bold red]DETECTED[/bold red]"
            severity   = f"[yellow]{d['severity']}[/yellow]"
            confidence = f"[white]{d['confidence']}%[/white]"
        else:
            status_str = "[green]CLEAR[/green]"
            severity   = "[dim]—[/dim]"
            confidence = "[dim]—[/dim]"
        dt.add_row(d["name"], status_str, severity, confidence)

    console.print(Panel(
        dt,
        title="[bold cyan] DEFECT ANALYSIS [/bold cyan]",
        border_style="cyan",
        padding=(0, 1),
    ))

    console.print()

    # ── Classification result panel ───────────────────────────────────────────
    grade_color = {"A": "green", "B": "yellow", "C": "red"}.get(grade, "white")
    grade_label = {
        "A": "Grade A  —  Healthy / Reusable",
        "B": "Grade B  —  Usable with Caution",
        "C": "Grade C  —  Not Fit for Reuse",
    }.get(grade, f"Grade {grade}")

    rt = Table(box=box.SIMPLE, show_header=False, padding=(0, 2), expand=False)
    rt.add_column("Label", style="bold white", width=22)
    rt.add_column("Value", width=50)

    rt.add_row("Battery ID",       battery_id)
    rt.add_row("Measured Voltage", f"{voltage:.2f} V")
    rt.add_row(
        "Classification",
        f"[bold {grade_color}]{grade_label}[/bold {grade_color}]"
    )
    rt.add_row(
        "Recommendation",
        f"[{grade_color}]{recommendation}[/{grade_color}]"
    )

    console.print(Panel(
        rt,
        title="[bold cyan] CLASSIFICATION RESULT [/bold cyan]",
        border_style=grade_color,
        padding=(0, 1),
    ))


# ─── Main menu ────────────────────────────────────────────────────────────────

def main():
    clear_screen()
    show_banner()

    while True:
        console.print()
        console.print(Panel(
            "  [bold white][1][/bold white]  Analyze Battery\n"
            "  [bold white][2][/bold white]  Exit",
            title="[bold cyan] MAIN MENU [/bold cyan]",
            border_style="cyan",
            padding=(1, 4),
            width=44,
        ))

        choice = Prompt.ask(
            "\n  [white]Select option[/white]",
            choices=["1", "2"],
        )

        if choice == "1":
            # ── Collect input ─────────────────────────────────────────────────
            image_path, battery_id, voltage = get_battery_input()

            console.print()
            console.print(Rule(" [bold cyan]ANALYSIS IN PROGRESS[/bold cyan] ", style="cyan"))
            console.print()

            # ── Stage 1: Image preprocessing ──────────────────────────────────
            prep_steps, image_data = preprocess_image(image_path)
            simulate_progress("Image preprocessing",  steps=4, delay=0.30)

            # ── Stage 2: Defect detection ──────────────────────────────────────
            defects = detect_defects(image_data, battery_id, voltage)
            simulate_progress("Defect detection",     steps=5, delay=0.22)

            # ── Stage 3: Battery classification ───────────────────────────────
            grade, recommendation = classify_battery(voltage, defects)
            simulate_progress("Battery classification", steps=3, delay=0.20)

            # ── Stage 4: Report generation ─────────────────────────────────────
            report_path = generate_report(
                battery_id, voltage, prep_steps, defects, grade, recommendation
            )
            simulate_progress("PDF report generation", steps=2, delay=0.30)

            # ── Display results ────────────────────────────────────────────────
            console.print()
            console.print(Rule(" [bold cyan]RESULTS[/bold cyan] ", style="cyan"))

            display_results(
                battery_id, voltage, prep_steps, defects, grade, recommendation
            )

            console.print()
            console.print(
                f"  [bold green]✓[/bold green]  Report saved → "
                f"[underline white]{report_path}[/underline white]"
            )
            console.print()
            show_separator()

        elif choice == "2":
            console.print()
            console.print("  [cyan]System exited.[/cyan]")
            console.print()
            sys.exit(0)


if __name__ == "__main__":
    main()
