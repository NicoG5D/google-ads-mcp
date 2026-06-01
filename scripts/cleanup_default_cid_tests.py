"""Remove the appended default_customer_id test sections from all test files."""
from pathlib import Path

MARKER = "\n\n# --- default customer_id variant ---\n\n"
TESTS_DIR = Path(__file__).parent.parent / "tests"

removed = []
for f in TESTS_DIR.glob("test_*.py"):
    text = f.read_text(encoding="utf-8")
    if MARKER in text:
        f.write_text(text.split(MARKER)[0] + "\n", encoding="utf-8")
        removed.append(f.name)

print(f"Cleaned {len(removed)} files")
