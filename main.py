"""Mandi Crop Sales & Price Tracker CLI and GUI launcher."""

import sys

from pymongo.errors import DuplicateKeyError, WriteError
from rich.panel import Panel

from analytics import (avg_price_per_crop_per_mandi, district_wise_quantity,
                       monthly_sales_trend, pending_payments_summary,
                       revenue_per_farmer, top_n_farmers, wheat_price_distribution)
from db import get_db
from seed_data import seed_all
from utils import console, print_table, format_inr
from validation_demo import run_validation_tests


def show_report(title: str, function, columns: list[tuple[str, str]]) -> None:
    """Run an analytics function and render a report with currency formatting."""
    rows = function()
    for row in rows:
        for key in ("total_revenue", "revenue", "pending_amount"):
            if key in row:
                row[key] = format_inr(row[key])
    print_table(title, rows, columns)


def main() -> None:
    """Start the interactive application."""
    if "--gui" in sys.argv:
        from gui import launch_gui
        launch_gui()
        return
    try:
        db = get_db()
    except Exception as exc:
        console.print(f"[bold red]MongoDB connection failed:[/] {exc}")
        console.print("Start MongoDB or set MONGO_URI before running the application.")
        return
    console.print(Panel.fit("[bold green]MANDI CROP SALES & PRICE TRACKER[/]\n[dim]From harvest records to smarter decisions[/]",
                            border_style="green"))
    while True:
        console.print("\n[bold cyan]1[/] Load Sample Data (reset DB)\n[bold cyan]2[/] Validation Demonstration\n"
                      "[bold cyan]3[/] Analytics Dashboard\n[bold cyan]4[/] Database Counts\n[bold cyan]0[/] Exit")
        choice = console.input("Choose an option: ").strip()
        try:
            if choice == "1":
                seed_all(db)
            elif choice == "2":
                run_validation_tests(db)
            elif choice == "3":
                console.print("\n[bold]Analytics Dashboard[/]")
                show_report("Revenue by Farmer", lambda: revenue_per_farmer(db),
                            [("farmer", "Farmer"), ("village", "Village"), ("total_revenue", "Revenue"), ("num_sales", "Sales")])
                show_report("Average Crop Prices", lambda: avg_price_per_crop_per_mandi(db),
                            [("crop", "Crop"), ("mandi", "Mandi"), ("avg_rate", "Avg Rate"), ("sales_count", "Sales")])
                show_report("Monthly Sales Trend", lambda: monthly_sales_trend(db),
                            [("_id", "Month"), ("total_quintals", "Quintals"), ("revenue", "Revenue"), ("avg_rate", "Avg Rate")])
                show_report("Top Farmers", lambda: top_n_farmers(db, 5),
                            [("farmer", "Farmer"), ("total_revenue", "Revenue"), ("total_quintals", "Quintals")])
                show_report("District-wise Quantity", lambda: district_wise_quantity(db),
                            [("_id", "Group"), ("total_quintals", "Quintals"), ("revenue", "Revenue")])
                show_report("Pending Payments", lambda: pending_payments_summary(db),
                            [("mandi", "Mandi"), ("pending_amount", "Outstanding"), ("sales", "Sales")])
                print_table("Wheat Rate Distribution", wheat_price_distribution(db))
            elif choice == "4":
                print_table("Database Counts", [{"collection": name, "records": db[name].count_documents({})}
                                                 for name in ("farmers", "mandis", "sales")])
            elif choice == "0":
                console.print("[green]Thank you for using Mandi Tracker. Happy farming![/]")
                break
            else:
                console.print("[yellow]Choose one of the displayed options.[/]")
        except (DuplicateKeyError, WriteError, ValueError) as exc:
            console.print(f"[red]Operation could not be completed:[/] {exc}")


if __name__ == "__main__":
    main()
