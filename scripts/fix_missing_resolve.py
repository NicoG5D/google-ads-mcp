"""Add customer_id = resolve_customer_id(customer_id) in method bodies
that have customer_id: Optional[str] = None but don't yet call resolve_customer_id.

Also fixes the positional call in remarketing_action_service.
"""

import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
SERVICES_DIR = ROOT / "src" / "services"


def add_resolve_calls(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    text = original

    # For each "try:\n<indent>" block inside a function that has
    # "customer_id: Optional[str] = None" in its signature but does NOT
    # already have "resolve_customer_id(customer_id)" in the body,
    # prepend the resolve call.
    #
    # Strategy: split text into method-like chunks by looking for
    # "customer_id: Optional[str] = None" preceding a try block.

    def patch_try_block(m: re.Match) -> str:
        before = m.string[: m.start()]
        # Check if this try block already has a resolve call recently before it
        recent = m.string[max(0, m.start() - 1500) : m.start()]
        if "resolve_customer_id(customer_id)" in recent:
            return m.group(0)
        # Check that customer_id: Optional[str] = None is in the recent context
        if "customer_id: Optional[str] = None" not in recent:
            return m.group(0)
        indent = m.group(1)
        return f"{indent}try:\n{indent}    customer_id = resolve_customer_id(customer_id)\n"

    text = re.sub(
        r"([ \t]+)try:\n",
        patch_try_block,
        text,
    )

    if text == original:
        return False
    path.write_text(text, encoding="utf-8")
    return True


TARGET_FILES = [
    "assets/asset_group_signal_service.py",
    "assets/customer_asset_service.py",
    "campaign/campaign_asset_set_service.py",
    "ad_group/ad_group_customizer_service.py",
]


def fix_remarketing_call(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    old = (
        "return await self._get_remarketing_action(\n"
        "                ctx, customer_id, remarketing_action_id\n"
        "            )"
    )
    new = (
        "return await self._get_remarketing_action(\n"
        "                ctx,\n"
        "                customer_id=customer_id,\n"
        "                remarketing_action_id=remarketing_action_id,\n"
        "            )"
    )
    if old in text:
        path.write_text(text.replace(old, new), encoding="utf-8")
        return True
    return False


def main() -> None:
    for rel in TARGET_FILES:
        p = SERVICES_DIR / Path(rel)
        if add_resolve_calls(p):
            print(f"Added resolve calls: {p.relative_to(ROOT)}")
        else:
            print(f"No change: {rel}")

    p = SERVICES_DIR / "audiences" / "remarketing_action_service.py"
    if fix_remarketing_call(p):
        print(f"Fixed positional call: {p.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
