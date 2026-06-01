"""Fix residual issues after migrate_customer_id.py:

1. Files where format_customer_id is still used for OTHER params but was removed from
   imports (customer_manager_link_service, customer_service).
2. Files where resolve_customer_id was added to imports but never called in the body —
   either add the call or remove the import.
3. Positional calls to methods that now have keyword-only params after *.
"""

import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
SERVICES_DIR = ROOT / "src" / "services"


def uses_in_body(text: str, name: str) -> bool:
    """Return True if `name(` appears in `text` (excluding import lines)."""
    body = re.sub(r"^from [^\n]+\n", "", text, flags=re.MULTILINE)
    body = re.sub(r"^import [^\n]+\n", "", body, flags=re.MULTILINE)
    return f"{name}(" in body


def fix_file(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    text = original

    # ── 1. Re-add format_customer_id to imports when body still uses it ─────
    if "format_customer_id(" in text and "format_customer_id" not in re.findall(
        r"from src\.utils import[^)]+\)", text, re.DOTALL
    ).__str__():
        # It's a single-line import or multi-line where it was dropped.
        def restore_format_cid(m: re.Match) -> str:
            block = m.group(0)
            if "format_customer_id" not in block and "format_customer_id(" in text:
                # Insert alongside resolve_customer_id
                block = block.replace(
                    "resolve_customer_id", "format_customer_id,\n    resolve_customer_id"
                )
            return block

        text = re.sub(
            r"from src\.utils import \([^)]*\)",
            restore_format_cid,
            text,
            flags=re.DOTALL,
        )

    # ── 2. Files with resolve_customer_id imported but never called ──────────
    if "resolve_customer_id" in text and not uses_in_body(text, "resolve_customer_id"):
        # If there's no customer_id param in any function, just drop the import.
        if "customer_id" not in text.replace("resolve_customer_id", "").replace(
            "format_customer_id", ""
        ):
            # No customer_id at all — drop the import entirely
            text = re.sub(r",?\s*resolve_customer_id", "", text)
            text = re.sub(r"resolve_customer_id,?\s*", "", text)
        else:
            # Has customer_id params — add resolve call at start of each method body
            # Pattern: right after a line with "customer_id: Optional[str] = None"
            # find the first "try:" inside that function and add the resolve call before it.
            def add_resolve_call(m: re.Match) -> str:
                indent = m.group(1)
                return f"{indent}customer_id = resolve_customer_id(customer_id)\n{m.group(0)}"

            # Add resolve call before first use of customer_id= in request constructors
            # or before the first try: block in methods that have customer_id param
            text = re.sub(
                r"([ \t]+)(customer_id=customer_id,)",
                lambda m: (
                    m.group(0)
                    if "customer_id = resolve_customer_id" in text[: m.start()]
                    or "customer_id = resolve_customer_id" in m.string[max(0, m.start()-500): m.start()]
                    else m.group(0)
                ),
                text,
            )
            # Simpler: prepend resolve call to any function body that has
            # customer_id: Optional and uses customer_id without resolving
            def add_resolve_in_method(m: re.Match) -> str:
                fn_sig = m.group(1)
                indent = m.group(2)
                docstring_or_body = m.group(3)
                if "resolve_customer_id(customer_id)" not in docstring_or_body:
                    return f'{fn_sig}\n{indent}customer_id = resolve_customer_id(customer_id)\n{indent}{docstring_or_body}'
                return m.group(0)

            text = re.sub(
                r'([ \t]*customer_id: Optional\[str\] = None,(?:[^\n]*\n)+?[ \t]*\) [^\n]*:\n)'
                r'([ \t]+)'
                r'((?:"""[^"]*"""\n[ \t]+)?)',
                add_resolve_in_method,
                text,
            )

    if text == original:
        return False
    path.write_text(text, encoding="utf-8")
    return True


def main() -> None:
    # ── Hard-code targeted fixes ─────────────────────────────────────────────

    # Fix 1: customer_manager_link_service — format_customer_id still used for
    # manager_customer_id, previous_manager_customer_id, new_manager_customer_id
    p = SERVICES_DIR / "account" / "customer_manager_link_service.py"
    text = p.read_text(encoding="utf-8")
    if "format_customer_id" not in text.split("from src.utils import")[1].split(")")[0]:
        text = text.replace(
            "    resolve_customer_id,",
            "    format_customer_id,\n    resolve_customer_id,",
        )
        p.write_text(text, encoding="utf-8")
        print(f"Fixed: {p.relative_to(ROOT)}")

    # Fix 2: customer_service — format_customer_id used for manager_customer_id
    p = SERVICES_DIR / "account" / "customer_service.py"
    text = p.read_text(encoding="utf-8")
    if "format_customer_id" not in text.split("from src.utils import")[1].split(")")[0]:
        text = text.replace(
            "    resolve_customer_id,",
            "    format_customer_id,\n    resolve_customer_id,",
        )
        p.write_text(text, encoding="utf-8")
        print(f"Fixed: {p.relative_to(ROOT)}")

    # Fix 3: remarketing_action_service — positional call to _get_remarketing_action
    p = SERVICES_DIR / "audiences" / "remarketing_action_service.py"
    text = p.read_text(encoding="utf-8")
    old = "return await self._get_remarketing_action(\n                ctx, customer_id, remarketing_action_id\n            )"
    new = "return await self._get_remarketing_action(\n                ctx,\n                customer_id=customer_id,\n                remarketing_action_id=remarketing_action_id,\n            )"
    if old in text:
        text = text.replace(old, new)
        p.write_text(text, encoding="utf-8")
        print(f"Fixed: {p.relative_to(ROOT)}")

    # Fix 4: files with resolve_customer_id imported but not used — remove import
    no_cid_files = [
        "targeting/geo_target_constant_service.py",
        "metadata/google_ads_field_service.py",
        "planning/keyword_theme_constant_service.py",
    ]
    for rel in no_cid_files:
        p = SERVICES_DIR / Path(rel)
        text = p.read_text(encoding="utf-8")
        if uses_in_body(text, "resolve_customer_id"):
            continue
        original = text
        # Remove from multi-line import
        text = re.sub(r",?\s*\bresolve_customer_id\b,?", "", text)
        # Clean up double commas or trailing commas before )
        text = re.sub(r",\s*\)", "\n)", text)
        text = re.sub(r"\(\s*,", "(", text)
        if text != original:
            p.write_text(text, encoding="utf-8")
            print(f"Fixed (removed unused import): {p.relative_to(ROOT)}")

    # Fix 5: files with resolve_customer_id imported but customer_id not resolved in body
    needs_resolve_call = [
        "assets/asset_group_signal_service.py",
        "assets/customer_asset_service.py",
        "campaign/campaign_asset_set_service.py",
        "ad_group/ad_group_customizer_service.py",
        "product_integration/third_party_app_analytics_link_service.py",
    ]
    for rel in needs_resolve_call:
        p = SERVICES_DIR / Path(rel)
        text = p.read_text(encoding="utf-8")
        original = text
        # In each method body that has customer_id param, add the resolve call
        # before the first usage of customer_id= in a constructor/request
        # Strategy: find "try:\n<indent>" blocks inside functions with customer_id
        # and insert the resolve call at the start of try block.
        text = re.sub(
            r"([ \t]+)(try:\n\s+)(?!customer_id = resolve_customer_id)",
            lambda m: (
                f"{m.group(1)}{m.group(2)}{m.group(1)}    customer_id = resolve_customer_id(customer_id)\n"
                if m.string[max(0, m.start()-800): m.start()].count("customer_id: Optional[str] = None") >
                   m.string[max(0, m.start()-800): m.start()].count("resolve_customer_id(customer_id)")
                else m.group(0)
            ),
            text,
        )
        if text != original:
            p.write_text(text, encoding="utf-8")
            print(f"Fixed (added resolve call): {p.relative_to(ROOT)}")
        else:
            print(f"No change needed or pattern not matched: {rel}")


if __name__ == "__main__":
    main()
