"""Migrate all service files to use resolve_customer_id instead of format_customer_id.

Changes applied to every file under src/services/:
  1. replace  format_customer_id(customer_id)  →  resolve_customer_id(customer_id)
  2. update   from src.utils import (...)       →  swap format_customer_id for resolve_customer_id
  3. replace  customer_id: str,                 →  customer_id: Optional[str] = None,
  4. insert   *,  after  ctx: Context,  so keyword-only params can follow an Optional default
  5. add      Optional  to typing imports if missing
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
SERVICES_DIR = ROOT / "src" / "services"


def migrate_file(path: Path) -> bool:
    """Return True if the file was modified."""
    original = path.read_text(encoding="utf-8")
    text = original

    # ── 1. swap format_customer_id(customer_id) ────────────────────────────
    text = text.replace(
        "format_customer_id(customer_id)",
        "resolve_customer_id(customer_id)",
    )

    # ── 2. update src.utils imports ────────────────────────────────────────
    def patch_utils_import(m: re.Match) -> str:
        block = m.group(0)
        if "format_customer_id" in block:
            block = block.replace("format_customer_id", "resolve_customer_id")
        elif "resolve_customer_id" not in block:
            block = re.sub(r"(\bget_logger\b)", r"resolve_customer_id,\n    \1", block, count=1)
        return block

    text = re.sub(
        r"from src\.utils import \([^)]*\)",
        patch_utils_import,
        text,
        flags=re.DOTALL,
    )

    def patch_single_line_import(m: re.Match) -> str:
        line = m.group(0)
        if "format_customer_id" in line:
            line = line.replace("format_customer_id", "resolve_customer_id")
        elif "resolve_customer_id" not in line:
            line = line.rstrip() + ", resolve_customer_id"
        return line

    text = re.sub(
        r"^from src\.utils import [^\n(][^\n]*$",
        patch_single_line_import,
        text,
        flags=re.MULTILINE,
    )

    # ── 3. customer_id: str,  →  customer_id: Optional[str] = None, ────────
    text = re.sub(
        r"(\s+)(customer_id): str,",
        r"\1\2: Optional[str] = None,",
        text,
    )

    # ── 4. insert  *,  before  customer_id: Optional[str] = None,  so
    #    keyword-only params can follow an Optional default without a SyntaxError.
    #    Two anchor patterns:
    #      a) after  ctx: Context,   (MCP tool functions)
    #      b) after  self,           (service class methods)
    def insert_kw_sep(m: re.Match) -> str:
        anchor = m.group(1)  # "    ctx: Context,"  or  "    self,"
        indent = m.group(2)  # leading whitespace of next line
        cid_line = m.group(3)  # "customer_id: Optional[str] = None,"
        return f"{anchor}\n{indent}*,\n{indent}{cid_line}"

    # After ctx: Context,
    text = re.sub(
        r"([ \t]*ctx: Context,)\n([ \t]+)(customer_id: Optional\[str\] = None,)",
        insert_kw_sep,
        text,
    )
    # After self,  (class methods — callers already use keyword args)
    text = re.sub(
        r"([ \t]*self,)\n([ \t]+)(customer_id: Optional\[str\] = None,)",
        insert_kw_sep,
        text,
    )
    # After opening "(" of a function def (no self, no ctx) — bare MCP tool fns.
    # Line ends with "(" optionally followed by a comment.
    def insert_kw_after_open(m: re.Match) -> str:
        def_open = m.group(1)  # "    async def foo(  # comment"
        indent = m.group(2)    # indentation of next line
        cid_line = m.group(3)  # "customer_id: Optional[str] = None,"
        return f"{def_open}\n{indent}*,\n{indent}{cid_line}"

    text = re.sub(
        r"([ \t]*(?:async )?def [^\n]+\([^\n]*)\n([ \t]+)(customer_id: Optional\[str\] = None,)",
        insert_kw_after_open,
        text,
    )

    # ── 5. ensure Optional is imported from typing ──────────────────────────
    if "Optional[str]" in text and "Optional" not in text.split("Optional[str]")[0]:
        def add_optional_multiline(m: re.Match) -> str:
            block = m.group(0)
            if "Optional" not in block:
                block = re.sub(
                    r"(\bAny\b|\bDict\b|\bList\b|\bCallable\b|\bTuple\b)",
                    r"Optional, \1",
                    block,
                    count=1,
                )
            return block

        text = re.sub(
            r"from typing import \([^)]*\)",
            add_optional_multiline,
            text,
            flags=re.DOTALL,
        )

        def add_optional_single(m: re.Match) -> str:
            line = m.group(0)
            if "Optional" not in line:
                line = re.sub(r"(from typing import )", r"\1Optional, ", line)
            return line

        text = re.sub(
            r"^from typing import [^\n(][^\n]*$",
            add_optional_single,
            text,
            flags=re.MULTILINE,
        )

    if text == original:
        return False

    path.write_text(text, encoding="utf-8")
    return True


def main() -> None:
    files = sorted(SERVICES_DIR.rglob("*.py"))
    modified = []
    for f in files:
        if migrate_file(f):
            modified.append(f.relative_to(ROOT))

    print(f"Modified {len(modified)} / {len(files)} files")
    for p in modified:
        print(f"  {p}")


if __name__ == "__main__":
    main()
