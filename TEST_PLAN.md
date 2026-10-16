# Test Plan & Strategy

## 1. Objective

Demonstrate an AI-assisted, bounded UI test execution agent that starts from a mock issue in the `Ready for QA` state, interprets acceptance criteria, interacts with a web application, verifies outcomes, and saves reproducible evidence.

## 2. Scope

**In scope**
- Local mock issue ingestion and RFQA state validation.
- LLM-generated structured test plan.
- LLM-guided semantic browser interaction using Playwright.
- Deterministic assertions for add-to-cart, cart badge, product name/price, and removal.
- Logs, screenshots, video, JSON result, and Markdown report.
- Manual trigger.

**Out of scope**
- Real GitHub API/webhook integration.
- Production credentials or real customer data.
- General-purpose arbitrary website automation.

## 3. Architecture

`mock_issue.json` → `issue_reader.py` → `test_planner.py` → `browser_agent.py` + Playwright → `assertions.py` → `reporter.py` → `evidence/run_*/`

- **Issue reader:** validates required fields, acceptance criteria, and the RFQA status.
- **Planner:** requests JSON-only test steps from OpenAI with a constrained system prompt and validates the returned schema.
- **Browser agent:** builds an inventory from visible controls and text. The model proposes one action at a time; Python checks the action allowlist and resolves it through semantic Playwright locators.
- **Assertions:** inspect actual page elements and compare them with the product details captured before interaction.
- **Reporter:** creates machine-readable and human-readable outcomes.

## 4. Prompt engineering and loop prevention

The planner is instructed to:
- Return JSON matching the required schema.
- Use only the supplied issue and acceptance criteria.
- Stay within a small number of steps.
- Never claim that a test passed.

The browser agent is instructed to:
- Use only the current UI inventory.
- Select one allowed action at a time.
- Never invent controls or claim an action succeeded before the browser confirms it.
- Return concise user-facing action summaries instead of hidden reasoning.

Runtime safeguards:
- Maximum of 8 browser-agent actions by default, configurable through `.env`.
- Repeated action-signature detection.
- Playwright action timeouts.
- One recovery attempt after a failed action.
- Strict action allowlist and target resolution.
- Exceptions are recorded in logs and reports.

## 5. Element identification

The agent receives a live inventory of visible buttons, links, inputs, and product names. It uses accessible roles and names where possible. Product-specific actions are resolved within the matching product card to avoid clicking the wrong duplicate `Add to cart` button. The LLM is never allowed to supply executable code or arbitrary selectors.

## 6. Assertions and truthfulness

The test oracle is deterministic Playwright inspection, not model confidence. The expected product name and price are captured from the first product card before interaction. The cart is then checked for:
- Exactly one cart item.
- Matching product name and price.
- Cart badge text `1`.
- Empty cart and no badge after removal.

A criterion is PASS only when observed UI state supports it. An unavailable API, browser, or target site is reported with an error and must not be misrepresented as a successful test.

## 7. Evidence

Each run records concise action logs, screenshots at key states and after actions, Playwright video, `result.json`, and `final_report.md`. Evidence paths are referenced by each criterion. No sample evidence is fabricated in the repository.

## 8. Exit criteria

A run-level PASS requires all required functional acceptance criteria to pass. Any failed assertion makes the run FAIL. An inability to begin meaningful execution is BLOCKED. The report must contain observed outcomes and evidence paths.
