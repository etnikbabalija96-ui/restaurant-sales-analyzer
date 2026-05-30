"""
Core analysis engine for restaurant sales data.
"""
from __future__ import annotations

import pandas as pd
from dataclasses import dataclass, field
from typing import Optional
import warnings

warnings.filterwarnings("ignore")


REQUIRED_COLUMNS = {"date", "item", "quantity", "unit_price"}
OPTIONAL_COLUMNS = {"category", "server", "table_number", "day_of_week", "time_of_day"}


@dataclass
class SalesReport:
    # Summary
    total_revenue: float = 0.0
    total_orders: int = 0
    avg_order_value: float = 0.0
    date_range: str = ""
    num_days: int = 0

    # Products
    top_items_by_revenue: pd.DataFrame = field(default_factory=pd.DataFrame)
    top_items_by_quantity: pd.DataFrame = field(default_factory=pd.DataFrame)
    worst_items: pd.DataFrame = field(default_factory=pd.DataFrame)
    category_breakdown: pd.DataFrame = field(default_factory=pd.DataFrame)

    # Time patterns
    revenue_by_day: pd.DataFrame = field(default_factory=pd.DataFrame)
    revenue_by_period: pd.DataFrame = field(default_factory=pd.DataFrame)
    best_day: str = ""
    worst_day: str = ""
    best_period: str = ""

    # Staff
    server_performance: Optional[pd.DataFrame] = None

    # Flags for available optional columns
    has_category: bool = False
    has_server: bool = False
    has_day_of_week: bool = False
    has_time_of_day: bool = False

    def to_dict(self) -> dict:
        """Serialize to a plain dict for AI context."""
        def df_to_list(df: pd.DataFrame, n: int = 10) -> list[dict]:
            if df is None or df.empty:
                return []
            return df.head(n).to_dict(orient="records")

        return {
            "summary": {
                "total_revenue": round(self.total_revenue, 2),
                "total_orders": self.total_orders,
                "avg_order_value": round(self.avg_order_value, 2),
                "date_range": self.date_range,
                "num_days": self.num_days,
                "daily_avg_revenue": round(self.total_revenue / max(self.num_days, 1), 2),
            },
            "top_items_by_revenue": df_to_list(self.top_items_by_revenue),
            "top_items_by_quantity": df_to_list(self.top_items_by_quantity),
            "worst_items": df_to_list(self.worst_items),
            "category_breakdown": df_to_list(self.category_breakdown),
            "revenue_by_day": df_to_list(self.revenue_by_day),
            "revenue_by_period": df_to_list(self.revenue_by_period),
            "best_day": self.best_day,
            "worst_day": self.worst_day,
            "best_period": self.best_period,
            "server_performance": df_to_list(self.server_performance) if self.server_performance is not None else None,
        }


def load_csv(filepath: str) -> pd.DataFrame:
    """Load and validate a sales CSV file."""
    try:
        df = pd.read_csv(filepath)
    except FileNotFoundError:
        raise ValueError(f"File not found: {filepath}")
    except Exception as e:
        raise ValueError(f"Could not read CSV: {e}")

    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(
            f"CSV is missing required columns: {missing}\n"
            f"Required: {REQUIRED_COLUMNS}\n"
            f"Found: {set(df.columns)}"
        )

    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0)
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce").fillna(0)
    df["revenue"] = df["quantity"] * df["unit_price"]

    try:
        df["date"] = pd.to_datetime(df["date"])
    except Exception:
        pass

    return df


def analyze(df: pd.DataFrame) -> SalesReport:
    """Run full analysis on a sales DataFrame. Returns a SalesReport."""
    report = SalesReport()

    # --- Detect optional columns ---
    report.has_category = "category" in df.columns
    report.has_server = "server" in df.columns
    report.has_day_of_week = "day_of_week" in df.columns
    report.has_time_of_day = "time_of_day" in df.columns

    # --- Summary ---
    report.total_revenue = df["revenue"].sum()
    report.total_orders = len(df)
    report.avg_order_value = df["revenue"].mean()

    if pd.api.types.is_datetime64_any_dtype(df["date"]):
        min_date = df["date"].min().strftime("%Y-%m-%d")
        max_date = df["date"].max().strftime("%Y-%m-%d")
        report.date_range = f"{min_date} to {max_date}"
        report.num_days = (df["date"].max() - df["date"].min()).days + 1
    else:
        unique_dates = df["date"].nunique()
        report.date_range = f"{unique_dates} unique dates"
        report.num_days = unique_dates

    # --- Items ---
    item_revenue = (
        df.groupby("item")["revenue"]
        .sum()
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
    item_revenue["revenue"] = item_revenue["revenue"].round(2)

    item_qty = (
        df.groupby("item")["quantity"]
        .sum()
        .reset_index()
        .sort_values("quantity", ascending=False)
    )

    report.top_items_by_revenue = item_revenue.head(10)
    report.top_items_by_quantity = item_qty.head(10)
    report.worst_items = item_revenue.tail(5).sort_values("revenue")

    # --- Category breakdown ---
    if report.has_category:
        cat = (
            df.groupby("category")
            .agg(revenue=("revenue", "sum"), orders=("quantity", "sum"))
            .reset_index()
            .sort_values("revenue", ascending=False)
        )
        cat["revenue"] = cat["revenue"].round(2)
        cat["revenue_pct"] = (cat["revenue"] / cat["revenue"].sum() * 100).round(1)
        report.category_breakdown = cat

    # --- Day of week ---
    if report.has_day_of_week:
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_rev = (
            df.groupby("day_of_week")["revenue"]
            .sum()
            .reindex(day_order)
            .dropna()
            .reset_index()
        )
        day_rev.columns = ["day", "revenue"]
        day_rev["revenue"] = day_rev["revenue"].round(2)
        report.revenue_by_day = day_rev
        report.best_day = day_rev.loc[day_rev["revenue"].idxmax(), "day"]
        report.worst_day = day_rev.loc[day_rev["revenue"].idxmin(), "day"]
    elif pd.api.types.is_datetime64_any_dtype(df["date"]):
        day_rev = (
            df.groupby(df["date"].dt.day_name())["revenue"]
            .sum()
            .reset_index()
            .sort_values("revenue", ascending=False)
        )
        day_rev.columns = ["day", "revenue"]
        day_rev["revenue"] = day_rev["revenue"].round(2)
        report.revenue_by_day = day_rev
        if not day_rev.empty:
            report.best_day = day_rev.iloc[0]["day"]
            report.worst_day = day_rev.iloc[-1]["day"]

    # --- Time of day ---
    if report.has_time_of_day:
        period_rev = (
            df.groupby("time_of_day")["revenue"]
            .sum()
            .reset_index()
            .sort_values("revenue", ascending=False)
        )
        period_rev.columns = ["period", "revenue"]
        period_rev["revenue"] = period_rev["revenue"].round(2)
        report.revenue_by_period = period_rev
        if not period_rev.empty:
            report.best_period = period_rev.iloc[0]["period"]

    # --- Server performance ---
    if report.has_server:
        server = (
            df.groupby("server")
            .agg(
                total_revenue=("revenue", "sum"),
                total_orders=("quantity", "sum"),
                avg_order_value=("revenue", "mean"),
            )
            .reset_index()
            .sort_values("total_revenue", ascending=False)
        )
        server["total_revenue"] = server["total_revenue"].round(2)
        server["avg_order_value"] = server["avg_order_value"].round(2)
        report.server_performance = server

    return report
