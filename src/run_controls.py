from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
LOGS_DIR = PROJECT_ROOT / "logs"

PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def create_exception(control, record_id, severity, details):
    return {
        "control_name": control,
        "record_id": record_id,
        "severity": severity,
        "details": details,
    }


gl = pd.read_csv(RAW_DATA_DIR / "gl_transactions.csv")
accounts = pd.read_csv(RAW_DATA_DIR / "chart_of_accounts.csv")
ap = pd.read_csv(RAW_DATA_DIR / "ap_subledger.csv")
close_tasks = pd.read_csv(RAW_DATA_DIR / "close_tasks.csv")

exceptions = []


# Control 1: Exact duplicate GL rows
duplicate_gl = gl[gl.duplicated(keep=False)]

for index, row in duplicate_gl.iterrows():
    exceptions.append(
        create_exception(
            "Duplicate GL transaction",
            f"GL row {index}",
            "High",
            f"Possible duplicate entry in journal {row['journal_id']}",
        )
    )


# Control 2: Invalid GL account numbers
valid_accounts = set(accounts["account_id"])
invalid_accounts = gl[~gl["account_id"].isin(valid_accounts)]

for index, row in invalid_accounts.iterrows():
    exceptions.append(
        create_exception(
            "Invalid account number",
            f"GL row {index}",
            "High",
            f"Account {row['account_id']} is not in the chart of accounts",
        )
    )


# Control 3: Unbalanced journal entries
journal_balances = (
    gl.groupby("journal_id", as_index=False)["amount"]
    .sum()
    .rename(columns={"amount": "journal_balance"})
)

unbalanced_journals = journal_balances[
    journal_balances["journal_balance"].abs() > 0.01
]

for _, row in unbalanced_journals.iterrows():
    exceptions.append(
        create_exception(
            "Unbalanced journal entry",
            row["journal_id"],
            "High",
            f"Journal is out of balance by ${row['journal_balance']:,.2f}",
        )
    )


# Control 4: Duplicate AP invoices
duplicate_invoices = ap[ap.duplicated(subset=["invoice_id"], keep=False)]

for index, row in duplicate_invoices.iterrows():
    exceptions.append(
        create_exception(
            "Duplicate AP invoice",
            row["invoice_id"],
            "High",
            f"Duplicate invoice found for {row['vendor_name']}",
        )
    )


# Control 5: Missing vendor names
missing_vendors = ap[
    ap["vendor_name"].isna()
    | (ap["vendor_name"].astype(str).str.strip() == "")
]

for _, row in missing_vendors.iterrows():
    exceptions.append(
        create_exception(
            "Missing vendor name",
            row["invoice_id"],
            "Medium",
            "Invoice does not have a valid vendor name",
        )
    )


# Control 6: Incomplete close tasks
incomplete_tasks = close_tasks[close_tasks["status"] != "Completed"]

for _, row in incomplete_tasks.iterrows():
    exceptions.append(
        create_exception(
            "Incomplete close task",
            row["task_name"],
            "Medium",
            f"Task owned by {row['owner']} has status: {row['status']}",
        )
    )


# Create detailed exception report
exception_report = pd.DataFrame(exceptions)
exception_report.to_csv(
    PROCESSED_DATA_DIR / "control_exceptions.csv",
    index=False,
)


# Create summary by control and severity
control_summary = (
    exception_report.groupby(
        ["control_name", "severity"], as_index=False
    )
    .size()
    .rename(columns={"size": "exception_count"})
)

control_summary.to_csv(
    PROCESSED_DATA_DIR / "control_summary.csv",
    index=False,
)


# Create readable audit log
with open(LOGS_DIR / "control_run.log", "w") as log:
    log.write("Financial Close Control Run\n")
    log.write("===========================\n")
    log.write(f"GL rows tested: {len(gl)}\n")
    log.write(f"AP invoices tested: {len(ap)}\n")
    log.write(f"Close tasks tested: {len(close_tasks)}\n")
    log.write(f"Total exceptions: {len(exception_report)}\n")


print("Financial controls completed successfully.")
print(f"Total exceptions identified: {len(exception_report)}")
print()
print(control_summary.to_string(index=False))