from datetime import datetime
from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parent
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

PIPELINE_LOG = LOGS_DIR / "pipeline_run.log"

steps = [
    ("Generate financial data", "src/generate_data.py"),
    ("Run financial controls", "src/run_controls.py"),
    ("Create management report", "src/create_reports.py"),
]


def run_step(step_name, script_path):
    print(f"\nRunning: {step_name}")

    result = subprocess.run(
        [sys.executable, script_path],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )

    with open(PIPELINE_LOG, "a") as log:
        log.write(f"\nSTEP: {step_name}\n")
        log.write(result.stdout)

        if result.stderr:
            log.write("\nERROR OUTPUT:\n")
            log.write(result.stderr)

    if result.returncode != 0:
        print(f"FAILED: {step_name}")
        print(result.stderr)
        sys.exit(result.returncode)

    print(result.stdout.strip())
    print(f"Completed: {step_name}")


def main():
    start_time = datetime.now()

    with open(PIPELINE_LOG, "w") as log:
        log.write("Financial Close Reporting Pipeline\n")
        log.write("==================================\n")
        log.write(
            f"Started: {start_time:%Y-%m-%d %H:%M:%S}\n"
        )

    print("Financial Close Reporting Pipeline")
    print("==================================")

    for step_name, script_path in steps:
        run_step(step_name, script_path)

    end_time = datetime.now()
    elapsed_time = end_time - start_time

    with open(PIPELINE_LOG, "a") as log:
        log.write(
            f"\nCompleted: {end_time:%Y-%m-%d %H:%M:%S}\n"
        )
        log.write(f"Elapsed time: {elapsed_time}\n")
        log.write("Pipeline status: SUCCESS\n")

    print("\n==================================")
    print("PIPELINE COMPLETED SUCCESSFULLY")
    print(f"Elapsed time: {elapsed_time}")
    print(
        "Report: "
        "reports/financial_close_controls_report.xlsx"
    )


if __name__ == "__main__":
    main()