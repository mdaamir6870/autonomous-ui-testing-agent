
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Check:
    id: str
    criterion: str
    status: str
    observed: str
    evidence: str


def safe_text(locator) -> str:
    try:
        return locator.inner_text(timeout=3000).strip()
    except Exception:
        return ""


def verify_cart_before_remove(page, expected_name: str, expected_price: str) -> list:
    item_count = (
        page.locator(".cart_item").count()
        if page.url.endswith("cart.html")
        else 0
    )
    actual_name = (
        safe_text(page.locator(".inventory_item_name").first)
        if item_count
        else ""
    )
    actual_price = (
        safe_text(page.locator(".inventory_item_price").first)
        if item_count
        else ""
    )
    badge = safe_text(page.locator(".shopping_cart_badge"))

    checks = [
        Check(
            "AC1",
            "A shopper can add an available product to the cart.",
            "PASS" if item_count == 1 else "FAIL",
            f"Observed cart item count: {item_count}",
            "screenshots/cart_before_remove.png",
        ),
        Check(
            "AC2",
            "The cart displays the selected product name and price.",
            "PASS"
            if actual_name == expected_name
            and actual_price == expected_price
            and bool(actual_name)
            else "FAIL",
            f"Observed name={actual_name!r}, price={actual_price!r}; "
            f"expected name={expected_name!r}, price={expected_price!r}",
            "screenshots/cart_before_remove.png",
        ),
        Check(
            "AC3",
            "The cart badge reflects one item after adding one product.",
            "PASS" if badge == "1" else "FAIL",
            f"Observed cart badge text: {badge!r}",
            "screenshots/cart_before_remove.png",
        ),
    ]
    return [asdict(check) for check in checks]


def verify_removal(page) -> dict:
    badge = safe_text(page.locator(".shopping_cart_badge"))
    item_count = (
        page.locator(".cart_item").count()
        if page.url.endswith("cart.html")
        else -1
    )
    passed = badge == "" and item_count == 0

    return asdict(
        Check(
            "AC4",
            "Removing the selected product empties the cart and clears the badge.",
            "PASS" if passed else "FAIL",
            f"Observed remaining items={item_count}; badge={badge!r}",
            "screenshots/cart_after_remove.png",
        )
    )


def verify_report_integrity(checks: list, run_dir: Path) -> dict:
    valid_statuses = {"PASS", "FAIL", "BLOCKED"}
    problems = []

    for check in checks:
        check_id = check.get("id", "Unknown check")

        if check.get("status") not in valid_statuses:
            problems.append(f"{check_id}: invalid status")

        if not check.get("observed"):
            problems.append(f"{check_id}: missing observation")

        evidence = check.get("evidence", "")
        if not evidence:
            problems.append(f"{check_id}: missing evidence path")
            continue

        # result.json is created later by the report writer.
        if check_id == "AC5" and evidence == "result.json":
            continue

        evidence_path = Path(evidence)

        if evidence_path.is_absolute() or ".." in evidence_path.parts:
            problems.append(f"{check_id}: unsafe evidence path")
            continue

        if not (run_dir / evidence_path).is_file():
            problems.append(
                f"{check_id}: evidence file not found: {evidence}"
            )

    valid = not problems
    observation = (
        f"Validated {len(checks)} checks and their evidence references."
        if valid
        else "Evidence integrity problems: " + "; ".join(problems)
    )

    return asdict(
        Check(
            "AC5",
            "Results are recorded from observed state with evidence files present.",
            "PASS" if valid else "FAIL",
            observation,
            "result.json",
        )
    )
