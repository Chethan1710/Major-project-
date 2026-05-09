# =============================================================================
# utils.py — Shared utilities: console, banner, separators, progress helpers
# Smart Battery Reuse Identification System
# =============================================================================

import os
import time

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text
from rich.progress import (
    Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
)

# One shared Console instance used across all modules
console = Console()


# ─── Display helpers ──────────────────────────────────────────────────────────

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def show_banner():
    """Print the project startup banner."""
    content = Text(justify="left")
    content.append("\n")
    content.append(
        "   SMART BATTERY REUSE IDENTIFICATION SYSTEM\n",
        style="bold cyan"
    )
    content.append(
        "   Battery Condition Analysis & Reuse Classification\n",
        style="white"
    )
    content.append("\n")
    content.append(
        "   Dept. of Electrical & Electronics Engineering\n",
        style="dim white"
    )
    content.append(
        "   Python  ·  OpenCV  ·  NumPy  ·  ReportLab   |   v1.0\n",
        style="dim cyan"
    )
    content.append("\n")

    console.print(
        Panel(content, border_style="cyan", padding=(0, 2))
    )


def show_separator(title: str = None):
    """Print a horizontal rule, optionally with a centered title."""
    if title:
        console.print(Rule(f" {title} ", style="cyan"))
    else:
        console.print(Rule(style="dim cyan"))


def confirm_step(label: str, ok: bool = True):
    """Print a single labelled step result (✓ or ✗)."""
    icon = "[green]✓[/green]" if ok else "[red]✗[/red]"
    console.print(f"  {icon}  {label}")


# ─── Animated progress bar ────────────────────────────────────────────────────

def simulate_progress(label: str, steps: int = 4, delay: float = 0.28):
    """
    Show an animated progress bar for a processing stage.
    The bar is transient — it disappears on completion and is replaced
    by a single confirmation line.
    """
    with Progress(
        SpinnerColumn(style="cyan"),
        TextColumn(f"  [cyan]{label}...[/cyan]"),
        BarColumn(bar_width=30, style="dim cyan", complete_style="cyan"),
        TaskProgressColumn(),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("", total=steps)
        for _ in range(steps):
            time.sleep(delay)
            progress.advance(task)

    confirm_step(label)
