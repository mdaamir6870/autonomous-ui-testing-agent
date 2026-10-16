
import logging
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from playwright.sync_api import sync_playwright

from src.issue_reader import load_issue
from src.test_planner import generate_plan
from src.browser_agent import bounded_explore
from src.assertions import (
    verify_cart_before_remove,
    verify_removal,
    verify_report_integrity,
)
from src.reporter import write_report


def configure_logger(run_dir: Path):
    logger = logging.getLogger("ui_agent")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    file_handler = logging.FileHandler(
        run_dir / "agent.log",
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def main():
    load_dotenv()

    run_dir = Path("evidence") / datetime.now().strftime(
        "run_%Y%m%d_%H%M%S"
    )
    (run_dir / "screenshots").mkdir(parents=True, exist_ok=True)
    (run_dir / "video").mkdir(parents=True, exist_ok=True)

    logger = configure_logger(run_dir)

    issue, plan, actions, checks, error = None, None, [], [], None

    try:
        issue = load_issue()

        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key or api_key == "your_api_key_here":
            raise RuntimeError(
                "OPENAI_API_KEY is missing. Add it to your .env file."
            )

        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        target_url = os.getenv("TARGET_URL", issue["target_url"])
        client = OpenAI(api_key=api_key)

        logger.info(
            "Validated issue %s with status %s.",
            issue["id"],
            issue["status"],
        )

        plan = generate_plan(client, model, issue)
        logger.info(
            "Planner created %d bounded steps: %s",
            len(plan["steps"]),
            plan.get("goal", ""),
        )

        headless = os.getenv("HEADLESS", "false").lower() == "true"
        max_actions = int(os.getenv("MAX_AGENT_ACTIONS", "8"))

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=headless)
            context = browser.new_context(
                record_video_dir=str(run_dir / "video")
            )
            page = context.new_page()
            page.set_default_timeout(8000)

            page.goto(
                target_url,
                wait_until="domcontentloaded",
                timeout=30000,
            )
            page.screenshot(
                path=str(run_dir / "screenshots" / "landing.png"),
                full_page=True,
                timeout=20000,
                animations="disabled",
            )
            logger.info("Opened target: %s", page.url)

            # Login and verify that the inventory page opens.
            page.get_by_role("textbox", name="Username").fill(
                "standard_user"
            )
            page.get_by_role("textbox", name="Password").fill(
                "secret_sauce"
            )
            page.get_by_role("button", name="Login").click()
            page.wait_for_url("**/inventory.html", timeout=15000)

            page.screenshot(
                path=str(run_dir / "screenshots" / "inventory.png"),
                full_page=True,
            )
            logger.info("Login verified: inventory page is visible.")

            # Capture the first product's expected name and price.
            first_card = page.locator(".inventory_item").first
            expected_name = (
                first_card.locator(".inventory_item_name")
                .inner_text(timeout=4000)
                .strip()
            )
            expected_price = (
                first_card.locator(".inventory_item_price")
                .inner_text(timeout=4000)
                .strip()
            )

            logger.info(
                "Captured expected first product: %s (%s)",
                expected_name,
                expected_price,
            )

            task = (
                f"Add the first product, {expected_name}, to the cart "
                "using its visible Add to cart button, then open the "
                "shopping cart. Do not remove the item."
            )

            actions = bounded_explore(
                client,
                model,
                page,
                task,
                run_dir,
                logger,
                max_actions=max_actions,
            )

            # Ensure the cart is open before checking its contents.
            if not page.url.endswith("cart.html"):
                cart_link = page.locator(".shopping_cart_link")

                if cart_link.count() == 1 and cart_link.is_visible():
                    logger.info(
                        "CHECKPOINT | Opening cart to verify actual state."
                    )
                    cart_link.click(timeout=8000)
                else:
                    logger.error(
                        "CHECKPOINT BLOCKED | Cart link is not uniquely visible."
                    )

            page.wait_for_timeout(400)

            page.screenshot(
                path=str(
                    run_dir / "screenshots" / "cart_before_remove.png"
                ),
                full_page=True,
                timeout=20000,
                animations="disabled",
            )

            checks = verify_cart_before_remove(
                page,
                expected_name,
                expected_price,
            )

            # Remove only when exactly one cart item and Remove button exist.
            item_count = (
                page.locator(".cart_item").count()
                if page.url.endswith("cart.html")
                else 0
            )
            remove_button = page.get_by_role(
                "button",
                name="Remove",
                exact=True,
            )
            remove_button_count = remove_button.count()

            if item_count == 1 and remove_button_count == 1:
                logger.info(
                    "REMOVAL | Attempting to remove product: %s",
                    expected_name,
                )

                remove_button.click(timeout=8000)
                page.wait_for_timeout(400)

                # Record the action; verify the outcome separately below.
                actions.append({
                    "action": "remove",
                    "observation": (
                        f"Clicked Remove for {expected_name}; "
                        "the cart state will be verified separately."
                    ),
                })

                logger.info(
                    "REMOVAL | Remove button click completed."
                )
            else:
                logger.error(
                    "REMOVAL BLOCKED | Expected one cart item and one "
                    "Remove button; observed items=%s, Remove buttons=%s",
                    item_count,
                    remove_button_count,
                )

            # Capture and verify the post-removal browser state.
            page.screenshot(
                path=str(
                    run_dir / "screenshots" / "cart_after_remove.png"
                ),
                full_page=True,
                timeout=20000,
                animations="disabled",
            )

            removal_check = verify_removal(page)
            checks.append(removal_check)

            logger.info(
                "REMOVAL RESULT | status=%s | %s",
                removal_check["status"],
                removal_check["observed"],
            )

            # Check that evidence references exist before adding AC5.
            integrity_check = verify_report_integrity(checks, run_dir)
            checks.append(integrity_check)

            logger.info(
                "REPORT INTEGRITY | status=%s | %s",
                integrity_check["status"],
                integrity_check["observed"],
            )

            context.close()  # Flush the video recording.
            browser.close()

    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        logger.exception("Execution stopped; see error details above.")

        if issue is None:
            issue = {
                "id": "UNKNOWN",
                "title": "Issue could not be loaded",
                "status": "unknown",
            }

        if not checks:
            checks = [
                {
                    "id": "RUN",
                    "criterion": (
                        "The agent begins execution and collects "
                        "browser evidence."
                    ),
                    "status": "BLOCKED",
                    "observed": error,
                    "evidence": "agent.log",
                }
            ]

    finally:
        issue = issue or {
            "id": "UNKNOWN",
            "title": "Unknown issue",
            "status": "unknown",
        }

        run_status = write_report(
            run_dir,
            issue,
            plan,
            checks,
            actions,
            error,
        )

        logger.info("FINAL RESULT: %s", run_status)
        print(f"\nRun result: {run_status}")
        print(f"Report: {(run_dir / 'final_report.md').resolve()}")
        print(f"Evidence folder: {run_dir.resolve()}")


if __name__ == "__main__":
    main()
