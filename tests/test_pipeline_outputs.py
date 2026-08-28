from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"


def test_control_exception_file_exists():
    exception_file = (
        PROCESSED_DIR / "control_exceptions.csv"
    )

    assert exception_file.exists()


def test_expected_exception_count():
    exceptions = pd.read_csv(
        PROCESSED_DIR / "control_exceptions.csv"
    )

    assert len(exceptions) == 12


def test_all_required_controls_ran():
    exceptions = pd.read_csv(
        PROCESSED_DIR / "control_exceptions.csv"
    )

    expected_controls = {
        "Duplicate GL transaction",
        "Invalid account number",
        "Unbalanced journal entry",
        "Duplicate AP invoice",
        "Missing vendor name",
        "Incomplete close task",
    }

    actual_controls = set(
        exceptions["control_name"].unique()
    )

    assert actual_controls == expected_controls


def test_high_severity_exceptions_exist():
    exceptions = pd.read_csv(
        PROCESSED_DIR / "control_exceptions.csv"
    )

    high_count = (
        exceptions["severity"] == "High"
    ).sum()

    assert high_count == 7


def test_excel_report_created():
    report_file = (
        REPORTS_DIR
        / "financial_close_controls_report.xlsx"
    )

    assert report_file.exists()
    assert report_file.stat().st_size > 0