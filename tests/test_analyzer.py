"""
Tests for the restaurant sales analyzer.
Run with: python -m pytest tests/ -v
"""
import pytest
import pandas as pd
import io
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from analysis.analyzer import load_csv, analyze, SalesReport, REQUIRED_COLUMNS


SAMPLE_CSV = """date,item,category,quantity,unit_price,server,day_of_week,time_of_day
2024-01-01,Margherita Pizza,Pizza,3,14.99,Alice,Monday,Dinner
2024-01-01,Caesar Salad,Salad,2,9.99,Alice,Monday,Dinner
2024-01-01,Tiramisu,Dessert,1,7.99,Bob,Monday,Dinner
2024-01-02,BBQ Burger,Burger,5,13.99,Carol,Tuesday,Lunch
2024-01-02,Fries,Sides,5,4.99,Carol,Tuesday,Lunch
2024-01-03,Seafood Linguine,Pasta,2,21.99,Alice,Wednesday,Dinner
2024-01-05,Margherita Pizza,Pizza,4,14.99,Bob,Friday,Dinner
2024-01-06,Pancakes,Breakfast,6,10.99,Carol,Saturday,Brunch
2024-01-06,Mimosa,Drinks,8,8.99,Carol,Saturday,Brunch
"""

MINIMAL_CSV = """date,item,quantity,unit_price
2024-01-01,Pizza,3,14.99
2024-01-02,Burger,5,13.99
"""

BAD_CSV_MISSING_COLS = """date,item
2024-01-01,Pizza
"""


def make_df(csv_text: str) -> pd.DataFrame:
    from analysis.analyzer import load_csv
    import tempfile, os
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(csv_text)
        tmppath = f.name
    try:
        df = load_csv(tmppath)
    finally:
        os.unlink(tmppath)
    return df


class TestLoadCSV:
    def test_loads_valid_csv(self):
        df = make_df(SAMPLE_CSV)
        assert len(df) == 9
        assert "revenue" in df.columns

    def test_revenue_computed(self):
        df = make_df(SAMPLE_CSV)
        row = df[df["item"] == "Margherita Pizza"].iloc[0]
        assert abs(row["revenue"] - 3 * 14.99) < 0.01

    def test_missing_required_columns_raises(self):
        with pytest.raises(ValueError, match="missing required columns"):
            make_df(BAD_CSV_MISSING_COLS)

    def test_minimal_csv_works(self):
        df = make_df(MINIMAL_CSV)
        assert len(df) == 2
        assert "revenue" in df.columns

    def test_columns_normalized(self):
        df = make_df(SAMPLE_CSV)
        for col in df.columns:
            assert col == col.lower()
            assert " " not in col

    def test_file_not_found_raises(self):
        with pytest.raises(ValueError, match="File not found"):
            load_csv("/nonexistent/path.csv")


class TestAnalyze:
    def setup_method(self):
        self.df = make_df(SAMPLE_CSV)
        self.report = analyze(self.df)

    def test_returns_sales_report(self):
        assert isinstance(self.report, SalesReport)

    def test_total_revenue_positive(self):
        assert self.report.total_revenue > 0

    def test_total_orders_matches_rows(self):
        assert self.report.total_orders == len(self.df)

    def test_avg_order_value_reasonable(self):
        assert 0 < self.report.avg_order_value < self.report.total_revenue

    def test_top_items_not_empty(self):
        assert len(self.report.top_items_by_revenue) > 0

    def test_top_items_sorted_descending(self):
        revenues = self.report.top_items_by_revenue["revenue"].tolist()
        assert revenues == sorted(revenues, reverse=True)

    def test_category_breakdown_present(self):
        assert self.report.has_category
        assert not self.report.category_breakdown.empty

    def test_category_revenue_sums_to_total(self):
        cat_total = self.report.category_breakdown["revenue"].sum()
        assert abs(cat_total - self.report.total_revenue) < 0.01

    def test_server_performance_present(self):
        assert self.report.has_server
        assert self.report.server_performance is not None
        assert not self.report.server_performance.empty

    def test_best_day_set(self):
        assert self.report.best_day != ""

    def test_best_period_set(self):
        assert self.report.best_period != ""

    def test_to_dict_serializable(self):
        import json
        d = self.report.to_dict()
        json.dumps(d)  # Should not raise

    def test_to_dict_has_summary(self):
        d = self.report.to_dict()
        assert "summary" in d
        assert d["summary"]["total_revenue"] > 0

    def test_minimal_csv_analyze(self):
        df = make_df(MINIMAL_CSV)
        report = analyze(df)
        assert report.total_revenue > 0
        assert not report.has_category
        assert not report.has_server

    def test_num_days_positive(self):
        assert self.report.num_days > 0


class TestReportContent:
    def setup_method(self):
        self.df = make_df(SAMPLE_CSV)
        self.report = analyze(self.df)

    def test_top_item_is_highest_revenue(self):
        top = self.report.top_items_by_revenue.iloc[0]["item"]
        top_rev = self.report.top_items_by_revenue.iloc[0]["revenue"]
        all_items = self.df.groupby("item")["revenue"].sum()
        assert abs(all_items[top] - top_rev) < 0.01

    def test_worst_items_are_lowest_revenue(self):
        worst_revs = self.report.worst_items["revenue"].tolist()
        all_revs = self.df.groupby("item")["revenue"].sum().sort_values().head(5).tolist()
        for rev in worst_revs:
            assert round(rev, 2) in [round(r, 2) for r in all_revs]

    def test_saturday_is_best_day(self):
        # Saturday has most items sold in sample data
        assert self.report.best_day == "Saturday"
