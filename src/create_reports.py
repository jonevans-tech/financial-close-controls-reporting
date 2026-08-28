from pathlib import Path

import pandas as pd


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# Load source data
# ---------------------------------------------------------
exceptions = pd.read_csv(
    PROCESSED_DIR / "control_exceptions.csv"
)

control_summary = pd.read_csv(
    PROCESSED_DIR / "control_summary.csv"
)

close_tasks = pd.read_csv(
    RAW_DIR / "close_tasks.csv"
)

gl = pd.read_csv(
    RAW_DIR / "gl_transactions.csv"
)

budget = pd.read_csv(
    RAW_DIR / "monthly_budget.csv"
)

report_path = (
    REPORTS_DIR / "financial_close_controls_report.xlsx"
)


# ---------------------------------------------------------
# Calculate executive metrics
# ---------------------------------------------------------
total_exceptions = len(exceptions)

high_exceptions = (
    exceptions["severity"] == "High"
).sum()

medium_exceptions = (
    exceptions["severity"] == "Medium"
).sum()

completed_tasks = (
    close_tasks["status"] == "Completed"
).sum()

total_tasks = len(close_tasks)

completion_rate = (
    completed_tasks / total_tasks
    if total_tasks > 0
    else 0
)


# ---------------------------------------------------------
# Prepare actual-versus-budget reporting
# ---------------------------------------------------------
gl["transaction_date"] = pd.to_datetime(
    gl["transaction_date"]
)

gl["period"] = gl[
    "transaction_date"
].dt.strftime("%Y-%m")

actuals = (
    gl[gl["account_id"] >= 5000]
    .groupby(
        ["period", "department", "account_id"],
        as_index=False,
    )["amount"]
    .sum()
    .rename(
        columns={"amount": "actual_amount"}
    )
)

variance = budget.merge(
    actuals,
    on=["period", "department", "account_id"],
    how="left",
)

variance["actual_amount"] = (
    variance["actual_amount"].fillna(0)
)

variance["variance_amount"] = (
    variance["budget_amount"]
    - variance["actual_amount"]
)

variance["variance_percent"] = (
    variance["variance_amount"]
    / variance["budget_amount"]
)


# ---------------------------------------------------------
# Create Excel report
# ---------------------------------------------------------
with pd.ExcelWriter(
    report_path,
    engine="xlsxwriter",
) as writer:

    workbook = writer.book

    # -----------------------------------------------------
    # Workbook formats
    # -----------------------------------------------------
    title_format = workbook.add_format(
        {
            "bold": True,
            "font_size": 18,
            "font_color": "white",
            "bg_color": "#1F4E78",
            "align": "center",
            "valign": "vcenter",
        }
    )

    section_format = workbook.add_format(
        {
            "bold": True,
            "font_size": 12,
            "font_color": "white",
            "bg_color": "#5B9BD5",
            "border": 1,
        }
    )

    metric_label_format = workbook.add_format(
        {
            "bold": True,
            "font_color": "#1F1F1F",
            "bg_color": "#D9EAF7",
            "border": 1,
        }
    )

    metric_value_format = workbook.add_format(
        {
            "bold": True,
            "font_size": 14,
            "align": "center",
            "border": 1,
        }
    )

    percent_metric_format = workbook.add_format(
        {
            "bold": True,
            "font_size": 14,
            "align": "center",
            "border": 1,
            "num_format": "0.0%",
        }
    )

    currency_format = workbook.add_format(
        {
            "num_format": "$#,##0.00",
        }
    )

    percentage_format = workbook.add_format(
        {
            "num_format": "0.0%",
        }
    )

    high_format = workbook.add_format(
        {
            "bg_color": "#F4CCCC",
            "font_color": "#9C0006",
        }
    )

    medium_format = workbook.add_format(
        {
            "bg_color": "#FFF2CC",
            "font_color": "#7F6000",
        }
    )

    completed_format = workbook.add_format(
        {
            "bg_color": "#D9EAD3",
            "font_color": "#274E13",
        }
    )

    incomplete_format = workbook.add_format(
        {
            "bg_color": "#FCE5CD",
            "font_color": "#783F04",
        }
    )

    action_format = workbook.add_format(
        {
            "bold": True,
            "bg_color": "#F4CCCC",
            "font_color": "#9C0006",
            "border": 1,
            "align": "center",
        }
    )

    pass_format = workbook.add_format(
        {
            "bold": True,
            "bg_color": "#D9EAD3",
            "font_color": "#274E13",
            "border": 1,
            "align": "center",
        }
    )

    wrap_format = workbook.add_format(
        {
            "text_wrap": True,
            "valign": "top",
        }
    )

    # -----------------------------------------------------
    # Executive Summary worksheet
    # -----------------------------------------------------
    executive = workbook.add_worksheet(
        "Executive Summary"
    )

    writer.sheets[
        "Executive Summary"
    ] = executive

    executive.hide_gridlines(2)

    executive.merge_range(
        "A1:H2",
        "Automated Financial Close & Controls Report",
        title_format,
    )

    executive.write(
        "A4",
        "Executive Control Metrics",
        section_format,
    )

    metrics = [
        (
            "Total Exceptions",
            total_exceptions,
        ),
        (
            "High-Severity Exceptions",
            high_exceptions,
        ),
        (
            "Medium-Severity Exceptions",
            medium_exceptions,
        ),
        (
            "Close Tasks Completed",
            completed_tasks,
        ),
        (
            "Total Close Tasks",
            total_tasks,
        ),
    ]

    row = 4

    for label, value in metrics:
        executive.write(
            row,
            0,
            label,
            metric_label_format,
        )

        executive.write(
            row,
            1,
            int(value),
            metric_value_format,
        )

        row += 1

    executive.write(
        row,
        0,
        "Close Completion Rate",
        metric_label_format,
    )

    executive.write(
        row,
        1,
        completion_rate,
        percent_metric_format,
    )

    executive.write(
        "D4",
        "Management Assessment",
        section_format,
    )

    executive.write(
        "D5",
        "Overall Status",
        metric_label_format,
    )

    if high_exceptions > 0:
        executive.write(
            "E5",
            "ACTION REQUIRED",
            action_format,
        )
    else:
        executive.write(
            "E5",
            "PASS",
            pass_format,
        )

    executive.write(
        "D6",
        "Primary Concern",
        metric_label_format,
    )

    executive.merge_range(
        "E6:H6",
        (
            "High-severity control exceptions "
            "require review."
        ),
        wrap_format,
    )

    executive.write(
        "D7",
        "Recommended Action",
        metric_label_format,
    )

    executive.merge_range(
        "E7:H8",
        (
            "Investigate duplicate transactions, "
            "invalid account activity, and "
            "unbalanced journal entries before "
            "completing the financial close."
        ),
        wrap_format,
    )

    executive.set_column("A:A", 28)
    executive.set_column("B:B", 18)
    executive.set_column("C:C", 3)
    executive.set_column("D:D", 24)
    executive.set_column("E:H", 18)

    executive.set_row(0, 25)
    executive.set_row(5, 30)
    executive.set_row(6, 42)

    executive.freeze_panes(3, 0)

    # -----------------------------------------------------
    # Write supporting worksheets
    # -----------------------------------------------------
    control_summary.to_excel(
        writer,
        sheet_name="Control Summary",
        startrow=2,
        index=False,
    )

    exceptions.to_excel(
        writer,
        sheet_name="Control Exceptions",
        startrow=2,
        index=False,
    )

    close_tasks.to_excel(
        writer,
        sheet_name="Close Checklist",
        startrow=2,
        index=False,
    )

    variance.to_excel(
        writer,
        sheet_name="Budget Variance",
        startrow=2,
        index=False,
    )

    sheet_data = {
        "Control Summary": control_summary,
        "Control Exceptions": exceptions,
        "Close Checklist": close_tasks,
        "Budget Variance": variance,
    }

    # -----------------------------------------------------
    # Format supporting worksheets
    # -----------------------------------------------------
    for sheet_name, dataframe in sheet_data.items():
        worksheet = writer.sheets[sheet_name]

        worksheet.hide_gridlines(2)

        rows, columns = dataframe.shape

        worksheet.merge_range(
            0,
            0,
            0,
            columns - 1,
            sheet_name,
            title_format,
        )

        worksheet.add_table(
            2,
            0,
            rows + 2,
            columns - 1,
            {
                "columns": [
                    {"header": column}
                    for column in dataframe.columns
                ],
                "style": "Table Style Medium 2",
            },
        )

        worksheet.freeze_panes(3, 0)

        for column_number, column_name in enumerate(
            dataframe.columns
        ):
            text_lengths = (
                dataframe[column_name]
                .fillna("")
                .astype(str)
                .map(len)
            )

            data_width = (
                text_lengths.max()
                if not text_lengths.empty
                else 0
            )

            column_width = max(
                len(str(column_name)),
                data_width,
            )

            worksheet.set_column(
                column_number,
                column_number,
                min(column_width + 3, 45),
            )

    # -----------------------------------------------------
    # Budget Variance formatting
    # -----------------------------------------------------
    variance_sheet = writer.sheets[
        "Budget Variance"
    ]

    variance_sheet.set_column(
        "D:F",
        16,
        currency_format,
    )

    variance_sheet.set_column(
        "G:G",
        16,
        percentage_format,
    )

    variance_sheet.conditional_format(
        3,
        5,
        len(variance) + 2,
        5,
        {
            "type": "cell",
            "criteria": "<",
            "value": 0,
            "format": high_format,
        },
    )

    # -----------------------------------------------------
    # Control Exception formatting
    # -----------------------------------------------------
    exceptions_sheet = writer.sheets[
        "Control Exceptions"
    ]

    exceptions_sheet.conditional_format(
        3,
        2,
        len(exceptions) + 2,
        2,
        {
            "type": "text",
            "criteria": "containing",
            "value": "High",
            "format": high_format,
        },
    )

    exceptions_sheet.conditional_format(
        3,
        2,
        len(exceptions) + 2,
        2,
        {
            "type": "text",
            "criteria": "containing",
            "value": "Medium",
            "format": medium_format,
        },
    )

    # -----------------------------------------------------
    # Close Checklist formatting
    # -----------------------------------------------------
    checklist_sheet = writer.sheets[
        "Close Checklist"
    ]

    checklist_sheet.conditional_format(
        3,
        3,
        len(close_tasks) + 2,
        3,
        {
            "type": "text",
            "criteria": "containing",
            "value": "Completed",
            "format": completed_format,
        },
    )

    checklist_sheet.conditional_format(
        3,
        3,
        len(close_tasks) + 2,
        3,
        {
            "type": "text",
            "criteria": "containing",
            "value": "In Progress",
            "format": incomplete_format,
        },
    )

    checklist_sheet.conditional_format(
        3,
        3,
        len(close_tasks) + 2,
        3,
        {
            "type": "text",
            "criteria": "containing",
            "value": "Not Started",
            "format": high_format,
        },
    )

    # -----------------------------------------------------
    # Executive chart
    # -----------------------------------------------------
    chart = workbook.add_chart(
        {"type": "column"}
    )

    last_summary_row = (
        len(control_summary) + 3
    )

    chart.add_series(
        {
            "name": "Exceptions",
            "categories": (
                "='Control Summary'!"
                f"$A$4:$A${last_summary_row}"
            ),
            "values": (
                "='Control Summary'!"
                f"$C$4:$C${last_summary_row}"
            ),
            "fill": {
                "color": "#5B9BD5",
            },
            "border": {
                "color": "#2F5597",
            },
            "data_labels": {
                "value": True,
            },
        }
    )

    chart.set_title(
        {
            "name": "Exceptions by Control",
        }
    )

    chart.set_x_axis(
        {
            "name": "Control",
            "label_position": "low",
        }
    )

    chart.set_y_axis(
        {
            "name": "Exception Count",
            "major_unit": 1,
            "min": 0,
        }
    )

    chart.set_legend(
        {
            "none": True,
        }
    )

    chart.set_style(10)

    executive.insert_chart(
        "A12",
        chart,
        {
            "x_scale": 1.4,
            "y_scale": 1.3,
        },
    )


print("Excel report created successfully:")
print(report_path)