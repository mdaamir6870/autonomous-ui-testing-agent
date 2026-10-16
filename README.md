# Autonomous UI Testing Agent

**Take-home assignment implementation — OpenAI API + Playwright**

This project simulates a GitHub issue that has entered **Ready for QA (RFQA)**, reads its acceptance criteria, asks an OpenAI model to propose a bounded test plan and browser action, executes the action through Playwright, verifies the real UI state, and creates an evidence bundle.

> This repository does not claim a test has passed until you run it. Screenshots, video, logs, and reports are generated at runtime.

## What it tests

Target: [SauceDemo](https://www.saucedemo.com/), a public e-commerce testing application.

- Log in using the site's public demo credentials.
- Add the first product to the cart through an AI-selected semantic UI action.
- Verify the cart contains the expected product and price.
- Verify the cart badge shows one item.
- Remove the item and verify the cart is empty.
- Save logs, screenshots, a browser video, JSON results, and a Markdown report.

## Requirements

- Python 3.10 or newer
- An OpenAI API key with API access
- Internet access to SauceDemo and the OpenAI API

## Quick start — Windows PowerShell

Open a terminal in the extracted project folder:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `.env` in VS Code and set your own API key. Then install Chromium:

```powershell
python -m playwright install chromium
```

Run:

```powershell
python -m src.main
```

If PowerShell blocks virtual-environment activation, run this in the same terminal and try activation again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Quick start — macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m playwright install chromium
python -m src.main
```

## Configuration

`.env.example` is a template. Copy it to `.env`; never put a real API key in source code or commit `.env`.

```dotenv
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini
TARGET_URL=https://www.saucedemo.com/
HEADLESS=false
MAX_AGENT_ACTIONS=8
```

`HEADLESS=false` opens a visible browser. Set it to `true` for headless runs.

## Project map

```text
autonomous-ui-testing-agent/
├── .env.example
├── .gitignore
├── README.md
├── TEST_PLAN.md
├── SCENARIOS.md
├── mock_issue.json
├── requirements.txt
├── docs/
│   └── LEARNING_GUIDE.md
├── src/
│   ├── __init__.py
│   ├── issue_reader.py
│   ├── test_planner.py
│   ├── browser_agent.py
│   ├── assertions.py
│   ├── reporter.py
│   └── main.py
├── tests/
│   └── test_issue_reader.py
└── evidence/
    └── README.md
```

## Architecture

1. **Issue reader:** validates the mock issue and checks that its state is `Ready for QA`.
2. **Test planner:** uses OpenAI to turn the user story and acceptance criteria into structured steps.
3. **Browser agent:** sends a live UI inventory to the model, validates its action against an allowlist, and executes it through Playwright.
4. **Assertion engine:** checks actual browser state. LLM narration is never accepted as proof.
5. **Reporter:** saves a Markdown summary, JSON results, logs, screenshots, and video.

## Reliability and guardrails

- The model can select only `click`, `inspect`, or `finish` actions for the browser feature flow.
- The model cannot run arbitrary Python, JavaScript, shell commands, CSS selectors, or XPath.
- Playwright locators use accessible roles and observed product names.
- An action budget and repeated-action guard prevent endless loops.
- Actions have timeouts; one recovery attempt is allowed for a failed model-selected action.
- PASS requires observed browser state; errors are recorded instead of being turned into false passes.
- Logs contain short action summaries, not private chain-of-thought.

## Run tests

```powershell
python -m pytest -q
```

The unit test checks issue parsing and RFQA status validation without calling OpenAI or launching a browser.

## Evidence

Each execution creates `evidence/run_YYYYMMDD_HHMMSS/` with:
- `agent.log`
- `screenshots/`
- `video/` (Playwright video, if the browser closes normally)
- `result.json`
- `final_report.md`

Review generated evidence before attaching it to your submission. The starter repository itself contains no fabricated execution report.

## GitHub issue trigger

`mock_issue.json` is the local mock GitHub issue. It represents the manual trigger required by this version of the assignment. The agent stops if the status is not `Ready for QA`. A real GitHub API integration or webhook is intentionally not included because the selected scope is manual execution.

## Publish to GitHub

1. Create a new empty repository on GitHub.
2. Open a terminal in this project directory.
3. Run:

```bash
git init
git add .
git status
git commit -m "Build autonomous UI testing agent"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/autonomous-ui-testing-agent.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username. Check `git status` before committing and make sure `.env` is not staged.

## Troubleshooting

- **Missing API key:** check that `.env` exists and `OPENAI_API_KEY` is set.
- **Chromium missing:** run `python -m playwright install chromium`.
- **Import errors:** ensure the virtual environment is active and run `pip install -r requirements.txt`.
- **Issue not RFQA:** edit `mock_issue.json` and set `"status": "Ready for QA"`.
- **Target website/API unavailable:** inspect `agent.log`; the report should explain the failure.
- **No video file visible immediately:** Playwright finalizes video when the browser context closes.

## Limitations

This is a focused take-home prototype, not a production test platform. The issue is a local mock rather than a real GitHub issue. SauceDemo's UI may change or be temporarily unavailable. Always inspect actual test results before submitting.
