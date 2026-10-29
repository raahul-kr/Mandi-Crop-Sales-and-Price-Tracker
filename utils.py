"""Input, formatting, and Rich presentation helpers."""

import json
import os
import sys
from datetime import datetime
from typing import Any, Iterable

from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table

if os.name == "nt" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
console = Console()


def ask_str(prompt: str, required: bool = True) -> str:
    """Read a trimmed string, repeating when a required value is empty."""
    while True:
        value = console.input(f"[bold cyan]{prompt}[/] ").strip()
        if value or not required:
            return value
        console.print("[red]This value is required.[/]")


def ask_float(prompt: str, minimum: float | None = None) -> float:
    """Read a floating-point number with optional lower-bound validation."""
    while True:
        try:
            value = float(ask_str(prompt))
            if minimum is not None and value < minimum:
                raise ValueError
            return value
        except ValueError:
            console.print("[red]Enter a valid number.[/]")


def ask_int(prompt: str, minimum: int | None = None) -> int:
    """Read an integer with optional lower-bound validation."""
    while True:
        try:
            value = int(ask_str(prompt))
            if minimum is not None and value < minimum:
                raise ValueError
            return value
        except ValueError:
            console.print("[red]Enter a valid whole number.[/]")


def ask_date(prompt: str, required: bool = True) -> datetime | None:
    """Read an ISO date and convert it to a MongoDB-compatible datetime."""
    while True:
        value = ask_str(f"{prompt} (YYYY-MM-DD)", required)
        if not value:
            return None
        try:
            return datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            console.print("[red]Use the YYYY-MM-DD format.[/]")


def format_inr(value: Any) -> str:
    """Format a numeric value as Indian Rupees."""
    return f"₹{float(value):,.2f}"


def pretty_json(value: Any) -> None:
    """Print a JSON query or aggregation pipeline with syntax highlighting."""
    console.print(Syntax(json.dumps(value, default=str, indent=2), "json", theme="monokai"))


def print_table(title: str, rows: Iterable[dict], columns: list[tuple[str, str]] | None = None) -> None:
    """Render dictionaries as a clean Rich table."""
    rows = list(rows)
    table = Table(title=title, title_style="bold green", header_style="bold magenta")
    if columns is None:
        keys = list(rows[0]) if rows else []
        columns = [(key, key.replace("_", " ").title()) for key in keys]
    for key, label in columns:
        table.add_column(label)
    for row in rows:
        table.add_row(*[str(row.get(key, "")) for key, _ in columns])
    console.print(table)
