"""
Manual CSV import guide for doboku-14w-training (Google Apps Script + Sheets DB).

This script does NOT upload anything automatically. It prints the steps needed to:
- Open the DB spreadsheet created by setup()
- Import QuestionBank CSV (optional)
- Import TestPlan14 CSV (optional)
"""

from __future__ import annotations

from pathlib import Path


SCRIPT_ID = "1giv21Jbc8lSmC8fQ3TDJ6gNP7-nH2m2KnPAYebhd0rK8B65gc0mvFzKS"
DEPLOY_URL = (
    "https://script.google.com/macros/s/"
    "AKfycbx9f7KnJ5WMuH3T3AWrewGaU14V5k8xn4uelGlxB9YFZyOL-So2IcF_D7J5jmggk-vYdg/exec"
)


def print_upload_instructions() -> None:
    tools_dir = Path(__file__).parent
    # Use Drive linking for images; keep imageUrl blank on import.
    questionbank_csv = tools_dir / "questionbank_drive_import.csv"
    testplan_csv = tools_dir / "testplan14.csv"

    print("=" * 70)
    print("GAS Database Import Instructions (doboku-14w-training)")
    print("=" * 70)
    print()

    print("Step 1: Open GAS Project and DB Spreadsheet")
    print("-------------------------------------------")
    print(f"1) GAS Editor: https://script.google.com/home/projects/{SCRIPT_ID}/edit")
    print("2) If DB is not created: run setup() once")
    print("3) Run checkDatabaseStatus() to get DB URL (dbUrl)")
    print("4) Open the dbUrl in browser (Google Sheets)")
    print()

    print("Step 2: Import QuestionBank CSV (Optional)")
    print("------------------------------------------")
    print(f"File: {questionbank_csv}")
    print("In DB spreadsheet: select 'QuestionBank' sheet, then:")
    print("- File -> Import -> Upload")
    print("- Import location: Replace current sheet")
    print("- Separator: Comma")
    print()
    print("Note: Importing a CSV with missing choices/correct answers will result in 0 valid questions.")
    print("      After import, use '?action=diagTestGen&testIndex=1' to confirm 'valid' > 0.")
    print()

    print("Step 3: Import TestPlan14 CSV (Optional)")
    print("----------------------------------------")
    print(f"File: {testplan_csv}")
    print("In DB spreadsheet: select 'TestPlan14' sheet, then:")
    print("- File -> Import -> Upload")
    print("- Import location: Replace current sheet")
    print("- Separator: Comma")
    print()

    print("Step 4: Verify (Recommended)")
    print("----------------------------")
    print("1) Open deploy URL:")
    print(f"   {DEPLOY_URL}")
    print("2) Diagnostics:")
    print("   - ?action=diagWeek")
    print("   - ?action=diagTestGen&testIndex=1")
    print()

    print("=" * 70)
    print("CSV Files")
    print("=" * 70)
    print(f"QuestionBank: {questionbank_csv}")
    print(f"TestPlan14:   {testplan_csv}")
    print("=" * 70)


def main() -> None:
    print_upload_instructions()


if __name__ == "__main__":
    main()
