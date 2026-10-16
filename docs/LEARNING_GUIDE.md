# Learning Guide — What each file does and why

## 1. `mock_issue.json`
This is the mock GitHub issue for the assignment. It stores the issue title, user story, RFQA status, target URL, and acceptance criteria. The agent reads these values instead of having the requirements scattered across Python files.

## 2. `src/issue_reader.py`
**Concept: input validation.** Before spending API calls or launching a browser, check that the issue has required fields and the correct state. If it is not `Ready for QA`, stop early.

## 3. `src/test_planner.py`
**Concept: LLM planning with structured output.** The OpenAI model converts the story and acceptance criteria into JSON test steps. JSON mode and Python validation make the output easier to inspect and reject if it does not match the expected schema. The plan is not itself proof that tests passed.

## 4. `src/browser_agent.py`
**Concept: observe → decide → act → observe.** Playwright gathers the current visible controls and text. The model chooses one allowed action. Python validates the action and resolves the target with semantic locators. A maximum action budget and duplicate-action check prevent an infinite loop.

## 5. `src/assertions.py`
**Concept: deterministic test oracle.** The expected product name and price are captured before interaction. After the agent adds the product, Playwright reads the cart and compares actual values with expected values. This prevents the model from declaring success without proof.

## 6. `src/reporter.py`
**Concept: audit trail.** The reporter writes the result as JSON for machines and Markdown for reviewers. Each criterion includes a status, observed value, and evidence path.

## 7. `src/main.py`
**Concept: orchestration.** This file connects the modules in the correct order: load issue → create plan → open browser → login → run bounded agent → assert → report. Keeping modules separate makes the project easier to test and explain.

## 8. `TEST_PLAN.md`
Explains the architecture, prompts, loop safeguards, element identification, assertions, evidence, and exit criteria.

## 9. `SCENARIOS.md`
Maps the mock issue's acceptance criteria to concrete browser checks. This lets a reviewer see exactly what the agent was asked to test.

## 10. `evidence/`
Generated evidence belongs here. Each run creates a timestamped subfolder. Do not manually invent screenshots or reports; run the code and submit the actual outputs.

## End-to-end mental model

1. **Read:** What does the issue require?
2. **Plan:** What steps could verify it?
3. **Observe:** What controls are actually on the page?
4. **Act:** Execute one validated action.
5. **Verify:** Did the browser state satisfy the criterion?
6. **Report:** Save evidence and an honest outcome.
