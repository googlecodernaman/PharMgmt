"""Tests for normalizer utilities."""

import pytest
from pharmgmt.parsing.normalizers import normalize_date, normalize_money, normalize_text, parse_quantity


class TestNormalizeDate:
    def test_dd_mm_yyyy(self):
        date, precision = normalize_date("01/06/2025")
        assert date == "2025-06-01"
        assert precision == "day"

    def test_dd_mm_yyyy_dash(self):
        date, precision = normalize_date("15-03-2025")
        assert date == "2025-03-15"
        assert precision == "day"

    def test_iso_format(self):
        date, precision = normalize_date("2025-06-01")
        assert date == "2025-06-01"
        assert precision == "day"

    def test_month_year(self):
        date, precision = normalize_date("06/2025")
        assert date == "2025-06-01"
        assert precision == "month"

    def test_month_name_year(self):
        date, precision = normalize_date("Jan 2025")
        assert date == "2025-01-01"
        assert precision == "month"

    def test_year_only(self):
        date, precision = normalize_date("2025")
        assert date == "2025-01-01"
        assert precision == "year"

    def test_empty(self):
        date, precision = normalize_date("")
        assert date is None

    def test_none(self):
        date, precision = normalize_date(None)
        assert date is None


class TestNormalizeMoney:
    def test_simple(self):
        assert normalize_money("125.50") == 12550

    def test_with_currency_symbol(self):
        assert normalize_money("₹1,250.00") == 125000

    def test_integer(self):
        assert normalize_money("1250") == 125000

    def test_with_dash(self):
        assert normalize_money("500/-") == 50000

    def test_empty(self):
        assert normalize_money("") is None

    def test_none(self):
        assert normalize_money(None) is None


class TestNormalizeText:
    def test_lowercase(self):
        assert normalize_text("PARACETAMOL 500MG") == "paracetamol 500mg"

    def test_whitespace_collapse(self):
        assert normalize_text("  hello   world  ") == "hello world"

    def test_empty(self):
        assert normalize_text("") == ""

    def test_none(self):
        assert normalize_text(None) == ""


class TestParseQuantity:
    def test_integer(self):
        assert parse_quantity("100") == 100

    def test_with_comma(self):
        assert parse_quantity("1,000") == 1000

    def test_float(self):
        assert parse_quantity("100.0") == 100

    def test_empty(self):
        assert parse_quantity("") is None
