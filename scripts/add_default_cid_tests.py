"""For each test file that calls a service with customer_id="...", add one test
variant that uses customer_id=None with the mock_default_customer_id fixture.

The new test is appended at the end of the file and follows the pattern:
  test_<original_name>_uses_default_customer_id
"""

import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
TESTS_DIR = ROOT / "tests"

# Files to skip (no service customer_id calls or already handled)
SKIP_FILES = {
    "conftest.py",
    "google_ads_test_utils.py",
    "__init__.py",
    "test_sdk_client.py",  # handled manually
    "test_customer_service.py",  # uses manager_customer_id, not the pattern
    "test_geo_target_constant_service.py",  # no customer_id param
    "test_google_ads_field_service.py",  # no customer_id param
}

# Match a complete async or sync test function that contains customer_id=
# We'll extract the first one from each file.
FN_PATTERN = re.compile(
    r'^( {0,4})((?:@pytest\.mark\.asyncio\n\1)?'
    r'(?:async )?def (test_\w+)\([^)]*\)[^:]*:\n'
    r'(?:(?!\n {0,4}(?:async )?def |\nclass ).+\n)*)',
    re.MULTILINE,
)


def has_customer_id_call(fn_body: str) -> bool:
    return bool(re.search(r'customer_id\s*=\s*["\']', fn_body))


def make_default_variant(fn_text: str, fn_name: str) -> str | None:
    """Return the test variant with customer_id=None and mock_default_customer_id fixture."""
    # Skip if already a default variant or if no customer_id= call
    if "default_customer_id" in fn_name:
        return None
    if not has_customer_id_call(fn_text):
        return None

    new_name = f"{fn_name}_uses_default_customer_id"

    # Replace customer_id="..." or customer_id='...' with customer_id=None
    new_body = re.sub(
        r'(customer_id\s*=\s*)["\'][^"\']*["\']',
        r"\1None",
        fn_text,
    )

    # Add mock_default_customer_id to function signature
    # Pattern: def test_XXX(  or  async def test_XXX(
    def _add_fixture(m: re.Match) -> str:
        params = m.group(2)
        # Strip trailing whitespace and trailing comma to avoid double comma
        params_clean = params.rstrip().rstrip(",")
        if params_clean.strip():
            new_params = params_clean + ",\n    mock_default_customer_id: None,"
        else:
            new_params = "mock_default_customer_id: None,"
        return m.group(1) + new_params + ")"

    new_body = re.sub(
        r'((?:async )?def ' + re.escape(fn_name) + r'\()([^)]*)\)',
        _add_fixture,
        new_body,
        count=1,
    )

    # Rename the function
    new_body = re.sub(
        r'((?:async )?def )' + re.escape(fn_name) + r'\b',
        r'\g<1>' + new_name,
        new_body,
        count=1,
    )

    return new_body


def process_file(path: Path) -> bool:
    if path.name in SKIP_FILES:
        return False

    text = path.read_text(encoding="utf-8")

    # Already processed
    if "uses_default_customer_id" in text:
        return False

    # Find the first test function with a customer_id= call
    chosen_fn_text = None
    chosen_fn_name = None

    for m in FN_PATTERN.finditer(text):
        fn_body = m.group(0)
        fn_name = m.group(3)
        if has_customer_id_call(fn_body):
            chosen_fn_text = fn_body
            chosen_fn_name = fn_name
            break

    # Also try class methods
    if chosen_fn_text is None:
        method_pat = re.compile(
            r'^( {4,8})((?:@pytest\.mark\.asyncio\n\1)?'
            r'(?:async )?def (test_\w+)\(self[^)]*\)[^:]*:\n'
            r'(?:(?!\n {4,8}(?:async )?def |\n {0,4}def |\nclass ).+\n)*)',
            re.MULTILINE,
        )
        for m in method_pat.finditer(text):
            fn_body = m.group(0)
            fn_name = m.group(3)
            if has_customer_id_call(fn_body):
                chosen_fn_text = fn_body
                chosen_fn_name = fn_name
                break

    if chosen_fn_text is None or chosen_fn_name is None:
        return False

    variant = make_default_variant(chosen_fn_text, chosen_fn_name)
    if variant is None:
        return False

    # Append to file
    separator = "\n\n# --- default customer_id variant ---\n\n"
    new_text = text.rstrip() + separator + variant.rstrip() + "\n"
    path.write_text(new_text, encoding="utf-8")
    return True


def main() -> None:
    files = sorted(TESTS_DIR.glob("test_*.py"))
    modified = []
    skipped = []

    for f in files:
        if process_file(f):
            modified.append(f.name)
        else:
            skipped.append(f.name)

    print(f"Modified {len(modified)} / {len(files)} files")
    for name in modified:
        print(f"  + {name}")
    if skipped:
        print(f"\nSkipped / no match ({len(skipped)}):")
        for name in skipped:
            print(f"  - {name}")


if __name__ == "__main__":
    main()
