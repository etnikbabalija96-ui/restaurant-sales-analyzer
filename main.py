#!/usr/bin/env python3
"""
Restaurant Sales Analyzer — CLI entry point.

Usage:
    python main.py data/sample_sales.csv
    python main.py data/sample_sales.csv --no-ai
    python main.py data/sample_sales.csv --output report.txt
"""
from __future__ import annotations

import sys
import os
from pathlib import Path

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from rich.columns import Columns
from rich.rule import Rule

load_dotenv()

from analysis.analyzer import load_csv, analyze, SalesReport
from analysis.ai_recommendations import get_recommendations

console = Console()


def print_summary(report: SalesReport) -> None:
    console.print()
    console.print(Rule("[bold]Sales Overview[/bold]", style="dim"))
    console.print()

    cards = [
        Panel(
            f"[bold green]${report.total_revenue:,.2f}[/bold green]\n[dim]Total Revenue[/dim]",
            expand=True,
        ),
        Panel(
            f"[bold cyan]{report.total_orders:,}[/bold cyan]\n[dim]Total Line Items[/dim]",
            expand=True,
        ),
        Panel(
            f"[bold yellow]${report.avg_order_value:.2f}[/bold yellow]\n[dim]Avg Line Value[/dim]",
            expand=True,
        ),
        Panel(
            f"[bold magenta]{report.num_days}[/bold magenta]\n[dim]Days of Data[/dim]",
            expand=True,
        ),
    ]
    console.print(Columns(cards, equal=True, expand=True))
    console.print()
    console.print(f"  [dim]Date range:[/dim] {report.date_range}")
    daily_avg = report.total_revenue / max(report.num_days, 1)
    console.print(f"  [dim]Daily avg revenue:[/dim] [green]${daily_avg:,.2f}[/green]")
    console.print()


def print_top_items(report: SalesReport) -> None:
    console.print(Rule("[bold]Top Items by Revenue[/bold]", style="dim"))
    console.print()

    table = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold")
    table.add_column("Item", style="white", min_width=20)
    table.add_column("Revenue", justify="right", style="green")
    table.add_column("Rank", justify="center", style="dim")

    for i, row in report.top_items_by_revenue.head(8).iterrows():
        rank = ["🥇", "🥈", "🥉"] + ["  "] * 10
        table.add_row(
            row["item"],
            f"${row['revenue']:,.2f}",
            rank[report.top_items_by_revenue.index.get_loc(i)],
        )

    console.print(table)


def print_categories(report: SalesReport) -> None:
    if report.category_breakdown.empty:
        return

    console.print(Rule("[bold]Revenue by Category[/bold]", style="dim"))
    console.print()

    table = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold")
    table.add_column("Category", style="white")
    table.add_column("Revenue", justify="right", style="green")
    table.add_column("Share", justify="right", style="cyan")
    table.add_column("Orders", justify="right", style="dim")

    for _, row in report.category_breakdown.iterrows():
        bar = "█" * int(row["revenue_pct"] / 5)
        table.add_row(
            row["category"],
            f"${row['revenue']:,.2f}",
            f"{row['revenue_pct']}% {bar}",
            str(int(row["orders"])),
        )

    console.print(table)


def print_day_analysis(report: SalesReport) -> None:
    if report.revenue_by_day.empty:
        return

    console.print(Rule("[bold]Revenue by Day of Week[/bold]", style="dim"))
    console.print()

    max_rev = report.revenue_by_day["revenue"].max()

    table = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold")
    table.add_column("Day", style="white", min_width=12)
    table.add_column("Revenue", justify="right", style="green")
    table.add_column("", min_width=30)

    for _, row in report.revenue_by_day.iterrows():
        bar_len = int(row["revenue"] / max_rev * 25)
        bar = "▓" * bar_len
        label = ""
        if row["day"] == report.best_day:
            label = " ← best"
            bar_color = "green"
        elif row["day"] == report.worst_day:
            label = " ← slowest"
            bar_color = "red"
        else:
            bar_color = "cyan"
        table.add_row(row["day"], f"${row['revenue']:,.2f}", f"[{bar_color}]{bar}[/{bar_color}]{label}")

    console.print(table)


def print_servers(report: SalesReport) -> None:
    if report.server_performance is None or report.server_performance.empty:
        return

    console.print(Rule("[bold]Server Performance[/bold]", style="dim"))
    console.print()

    table = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold")
    table.add_column("Server", style="white")
    table.add_column("Revenue", justify="right", style="green")
    table.add_column("Items Sold", justify="right", style="cyan")
    table.add_column("Avg per Line", justify="right", style="yellow")

    for _, row in report.server_performance.iterrows():
        table.add_row(
            row["server"],
            f"${row['total_revenue']:,.2f}",
            str(int(row["total_orders"])),
            f"${row['avg_order_value']:.2f}",
        )

    console.print(table)


def print_underperformers(report: SalesReport) -> None:
    if report.worst_items.empty:
        return

    console.print(Rule("[bold]Lowest Revenue Items[/bold]", style="dim"))
    console.print()

    table = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold")
    table.add_column("Item", style="white")
    table.add_column("Revenue", justify="right", style="red")

    for _, row in report.worst_items.iterrows():
        table.add_row(row["item"], f"${row['revenue']:,.2f}")

    console.print(table)


def print_ai_recommendations(report: SalesReport) -> None:
    console.print()
    console.print(Rule("[bold]AI Recommendations[/bold]", style="dim"))
    console.print()
    console.print("[dim]Analyzing your data with Claude...[/dim]")
    console.print()

    try:
        recs = get_recommendations(report)
        console.print(Panel(recs, border_style="blue", padding=(1, 2)))
    except EnvironmentError as e:
        console.print(f"[yellow]⚠ Skipping AI recommendations: {e}[/yellow]")
    except Exception as e:
        console.print(f"[red]✗ AI error: {e}[/red]")


@click.command()
@click.argument("csv_file", type=click.Path(exists=True))
@click.option("--no-ai", is_flag=True, default=False, help="Skip AI recommendations (no API key needed).")
@click.option("--output", "-o", default=None, help="Save text report to a file.")
def main(csv_file: str, no_ai: bool, output: str | None) -> None:
    """
    Analyze restaurant sales data from a CSV file.

    CSV_FILE should have columns: date, item, quantity, unit_price
    Optional: category, server, table_number, day_of_week, time_of_day
    """
    # Capture output to file if requested
    if output:
        file_console = Console(file=open(output, "w"), highlight=False)
        capture = True
    else:
        file_console = None
        capture = False

    console.print()
    console.print(
        Panel.fit(
            "[bold white]Restaurant Sales Analyzer[/bold white]\n[dim]Business intelligence from your CSV[/dim]",
            border_style="green",
        )
    )

    # Load
    console.print(f"\n[dim]Loading[/dim] [cyan]{csv_file}[/cyan]...")
    try:
        df = load_csv(csv_file)
    except ValueError as e:
        console.print(f"[red]✗ {e}[/red]")
        sys.exit(1)

    console.print(f"[green]✓[/green] Loaded [bold]{len(df):,}[/bold] rows")

    # Analyze
    console.print("[dim]Running analysis...[/dim]")
    report = analyze(df)
    console.print("[green]✓[/green] Analysis complete\n")

    # Print all sections
    print_summary(report)
    print_top_items(report)
    print_categories(report)
    print_day_analysis(report)
    print_servers(report)
    print_underperformers(report)

    if not no_ai:
        print_ai_recommendations(report)
    else:
        console.print("\n[dim]Skipping AI recommendations (--no-ai flag set)[/dim]")

    console.print()
    console.print(Rule(style="dim"))
    console.print("[dim]Done.[/dim]\n")

    if output and file_console:
        console.print(f"[dim]Report saved to[/dim] [cyan]{output}[/cyan]")


if __name__ == "__main__":
    main()
