from pathlib import Path
import random

import numpy as np
import pandas as pd
from faker import Faker


# Reproducible results
random.seed(42)
np.random.seed(42)
fake = Faker()
Faker.seed(42)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)


# Chart of accounts
accounts = pd.DataFrame(
    [
        [1000, "Cash", "Asset"],
        [1100, "Accounts Receivable", "Asset"],
        [1200, "Prepaid Expenses", "Asset"],
        [2000, "Accounts Payable", "Liability"],
        [2100, "Accrued Expenses", "Liability"],
        [3000, "Retained Earnings", "Equity"],
        [4000, "Product Revenue", "Revenue"],
        [4100, "Service Revenue", "Revenue"],
        [5000, "Cost of Goods Sold", "Expense"],
        [6100, "Salaries and Benefits", "Expense"],
        [6200, "Software Expense", "Expense"],
        [6300, "Marketing Expense", "Expense"],
        [6400, "Professional Services", "Expense"],
        [6500, "Travel Expense", "Expense"],
    ],
    columns=["account_id", "account_name", "account_type"],
)

accounts.to_csv(RAW_DATA_DIR / "chart_of_accounts.csv", index=False)


# General ledger transactions
departments = ["Finance", "Operations", "Sales", "Technology", "Marketing"]
expense_accounts = [5000, 6100, 6200, 6300, 6400, 6500]
offset_accounts = [1000, 2000, 2100]

gl_rows = []
journal_number = 10000

for month in range(1, 13):
    for _ in range(50):
        journal_number += 1
        transaction_date = fake.date_between_dates(
            date_start=pd.Timestamp(2026, month, 1).date(),
            date_end=(pd.Timestamp(2026, month, 1) + pd.offsets.MonthEnd(0)).date(),
        )

        amount = round(random.uniform(500, 25000), 2)
        department = random.choice(departments)
        expense_account = random.choice(expense_accounts)
        offset_account = random.choice(offset_accounts)

        # Debit
        gl_rows.append(
            [
                f"JE-{journal_number}",
                transaction_date,
                expense_account,
                department,
                amount,
                "Debit",
                fake.sentence(nb_words=4),
            ]
        )

        # Matching credit
        gl_rows.append(
            [
                f"JE-{journal_number}",
                transaction_date,
                offset_account,
                department,
                -amount,
                "Credit",
                fake.sentence(nb_words=4),
            ]
        )

gl = pd.DataFrame(
    gl_rows,
    columns=[
        "journal_id",
        "transaction_date",
        "account_id",
        "department",
        "amount",
        "entry_type",
        "description",
    ],
)

# Deliberately introduce exceptions for later control testing
gl = pd.concat([gl, gl.iloc[[10]]], ignore_index=True)
gl.loc[25, "account_id"] = 9999
gl.loc[40, "amount"] = gl.loc[40, "amount"] + 125.00

gl.to_csv(RAW_DATA_DIR / "gl_transactions.csv", index=False)


# Accounts payable subledger
vendors = [fake.company() for _ in range(20)]
ap_rows = []

for invoice_number in range(1, 301):
    invoice_date = fake.date_between(
        start_date=pd.Timestamp("2026-01-01").date(),
        end_date=pd.Timestamp("2026-12-31").date(),
    )

    invoice_amount = round(random.uniform(250, 15000), 2)

    ap_rows.append(
        [
            f"INV-{invoice_number:05d}",
            random.choice(vendors),
            invoice_date,
            invoice_amount,
            random.choice(departments),
            random.choice(["Paid", "Open", "Posted"]),
        ]
    )

ap = pd.DataFrame(
    ap_rows,
    columns=[
        "invoice_id",
        "vendor_name",
        "invoice_date",
        "invoice_amount",
        "department",
        "status",
    ],
)

# Additional exceptions
ap = pd.concat([ap, ap.iloc[[5]]], ignore_index=True)
ap.loc[12, "vendor_name"] = ""

ap.to_csv(RAW_DATA_DIR / "ap_subledger.csv", index=False)


# Monthly departmental budget
budget_rows = []

for month in range(1, 13):
    for department in departments:
        for account_id in expense_accounts:
            budget_rows.append(
                [
                    f"2026-{month:02d}",
                    department,
                    account_id,
                    round(random.uniform(5000, 80000), 2),
                ]
            )

budget = pd.DataFrame(
    budget_rows,
    columns=["period", "department", "account_id", "budget_amount"],
)

budget.to_csv(RAW_DATA_DIR / "monthly_budget.csv", index=False)


# Month-end close checklist
close_tasks = pd.DataFrame(
    [
        ["Bank reconciliations", "Finance", "2026-12-31", "Completed"],
        ["Accounts payable close", "Finance", "2026-12-31", "Completed"],
        ["Accounts receivable close", "Finance", "2026-12-31", "In Progress"],
        ["Payroll accrual", "Finance", "2026-12-31", "Not Started"],
        ["Revenue review", "Sales", "2026-12-31", "Completed"],
        ["Expense variance review", "Operations", "2026-12-31", "In Progress"],
        ["Management report review", "Finance", "2026-12-31", "Not Started"],
    ],
    columns=["task_name", "owner", "due_date", "status"],
)

close_tasks.to_csv(RAW_DATA_DIR / "close_tasks.csv", index=False)


print("Financial datasets created successfully:")
for file_path in sorted(RAW_DATA_DIR.glob("*.csv")):
    print(f"  {file_path.name}")