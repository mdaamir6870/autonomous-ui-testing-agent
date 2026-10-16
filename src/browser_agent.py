import json
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

AGENT_PROMPT = """You are a bounded browser interaction agent. Return exactly one JSON object:
{"action":"click|inspect|finish","target":"visible control description","reason":"short action summary"}.
Use only controls in the live UI inventory. The task is to add the FIRST product to the cart and open the cart. If multiple Add to cart buttons exist, select the one belonging to the first product card. Never invent controls, claim success before observing it, or use code/CSS/XPath/arbitrary commands. Keep the reason concise and user-facing."""


def get_inventory(page) -> dict:
    """Collect current visible UI controls and product names for the LLM."""
    controls = page.locator("button, a, input, [role=button], [role=link]").evaluate_all(
        """els => els.filter(e => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length))
          .slice(0, 80).map(e => {
            const card = e.closest('.inventory_item');
            const product = card ? (card.querySelector('.inventory_item_name')?.innerText || '').trim() : '';
            const raw = (e.getAttribute('aria-label') || e.getAttribute('placeholder') ||
                         e.innerText || e.value || '').trim();
            return {
              role: e.getAttribute('role') || (e.tagName === 'BUTTON' ? 'button' :
                    e.tagName === 'A' ? 'link' : e.tagName === 'INPUT' ? 'input' : ''),
              name: product && raw.toLowerCase().includes('add to cart')
                    ? `Add to cart for ${product}` : raw.slice(0, 100),
              product: product,
              disabled: !!e.disabled
            };
          })"""
    )
    return {
        "url": page.url,
        "title": page.title(),
        "controls": controls,
        "visible_text": page.locator("body").inner_text(timeout=5000)[:4000],
    }


def ask_for_action(client, model: str, task: str, ui: dict, history: list) -> dict:
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": AGENT_PROMPT},
            {"role": "user", "content": json.dumps({
                "task": task, "live_ui": ui, "recent_actions": history[-5:]
            })},
        ],
        timeout=45,
    )
    action = json.loads(response.choices[0].message.content)
    if action.get("action") not in {"click", "inspect", "finish"}:
        raise ValueError(f"Agent returned unsupported action: {action}")
    if action["action"] == "click" and not action.get("target"):
        raise ValueError("Agent click action has no target.")
    return action


def resolve_target(page, target: str):
    """Resolve model-described targets using observed names and semantic locators."""
    target = target.strip()
    prefix = "Add to cart for "
    if target.startswith(prefix):
        product_name = target[len(prefix):].strip()
        card = page.locator(".inventory_item").filter(
            has=page.get_by_text(product_name, exact=True)
        )
        if card.count() == 1:
            button = card.get_by_role("button", name="Add to cart", exact=True)
            if button.count() == 1:
                return button

    for role in ("button", "link"):
        locator = page.get_by_role(role, name=target, exact=True)
        if locator.count() == 1:
            return locator

    locator = page.get_by_text(target, exact=True)
    return locator if locator.count() == 1 else None


def execute_click(page, target: str) -> str:
    locator = resolve_target(page, target)
    if locator is None:
        raise ValueError(f"Could not uniquely resolve target from current UI: {target!r}")
    locator.click(timeout=8000)
    return f"Clicked observed semantic target: {target}"


def bounded_explore(client, model, page, task, run_dir, logger, max_actions=8) -> list:
    """Run a bounded agent loop; stop on finish, duplicate action, or failure."""
    history, seen = [], set()
    for step_number in range(1, max_actions + 1):
        action = ask_for_action(client, model, task, get_inventory(page), history)
        signature = (action.get("action"), action.get("target"))
        logger.info(
            "STEP %02d | action=%s | target=%s | summary=%s",
            step_number, action.get("action"), action.get("target", ""),
            action.get("reason", "No summary supplied."),
        )
        if action["action"] == "finish":
            logger.info("Agent selected finish.")
            break
        if action["action"] == "inspect":
            history.append({"action": "inspect", "observation": "Refreshed live UI inventory."})
            continue
        if signature in seen:
            logger.warning("Repeated action detected; stopping to prevent a loop: %s", signature)
            break
        seen.add(signature)

        try:
            observation = execute_click(page, action["target"])
        except (PlaywrightTimeoutError, ValueError) as first_error:
            logger.warning("Action failed; one recovery attempt will be allowed: %s", first_error)
            try:
                recovery = ask_for_action(client, model, task, get_inventory(page), history)
                recovery_sig = (recovery.get("action"), recovery.get("target"))
                if recovery.get("action") != "click" or recovery_sig == signature or recovery_sig in seen:
                    raise ValueError("Recovery did not propose a new, allowed click.")
                observation = execute_click(page, recovery["target"])
                action = recovery
                seen.add(recovery_sig)
            except Exception as recovery_error:
                logger.error("Recovery attempt failed: %s", recovery_error)
                history.append({"action": action, "observation": f"FAILED: {recovery_error}"})
                break

        page.wait_for_timeout(400)
        screenshot = run_dir / "screenshots" / f"step_{step_number:02d}.png"
        page.screenshot(path=str(screenshot), full_page=True)
        logger.info("OBSERVED | %s | screenshot=%s", observation, screenshot.name)
        history.append({"action": action, "observation": observation})
        if page.url.endswith("cart.html"):
            break
    else:
        logger.warning("Maximum browser action budget reached (%s).", max_actions)
    return history
