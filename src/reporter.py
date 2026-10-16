
import json
from datetime import datetime, timezone


def write_report(run_dir, issue, plan, checks, actions, error=None):
    # A runtime error must never be reported as a successful run.
    if error:
        run_status = "BLOCKED" if not checks else "FAIL"
    elif checks and all(check.get("status") == "PASS" for check in checks):
        run_status = "PASS"
    else:
        run_status = "FAIL"

    result = {
        "issue_id": issue.get("id"),
        "issue_title": issue.get("title"),
        "issue_status": issue.get("status"),
        "run_status": run_status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "error": error,
        "plan": plan,
        "checks": checks,
        "actions": actions,
    }

    (run_dir / "result.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    lines = [
        "# Autonomous UI Test Execution Report",
        "",
        f"- **Issue:** {issue.get('id')} — {issue.get('title')}",
        f"- **Issue state:** {issue.get('status')}",
        f"- **Run result:** **{run_status}**",
        f"- **Generated (UTC):** {result['generated_at_utc']}",
        "",
        "## Acceptance criteria results",
        "",
        "| ID | Status | Criterion | Observed result | Evidence |",
        "|---|---|---|---|---|",
    ]

    for check in checks:
        def clean(value):
            return str(value).replace("|", "/").replace("\n", " ")

        lines.append(
            f"| {clean(check.get('id', 'UNKNOWN'))} "
            f"| **{clean(check.get('status', 'UNKNOWN'))}** "
            f"| {clean(check.get('criterion', ''))} "
            f"| {clean(check.get('observed', ''))} "
            f"| `{clean(check.get('evidence', ''))}` |"
        )

    lines += ["", "## Agent actions", ""]

    if actions:
        for index, item in enumerate(actions, 1):
            action = item.get("action", "unknown")
            observation = item.get("observation", "")
            if isinstance(action, dict):
                action = action.get("action", "unknown")
            lines.append(f"{index}. `{action}` — {observation}")
    else:
        lines.append("No agent browser actions completed.")

    if error:
        lines += [
            "",
            "## Error / blocking reason",
            "",
            "```text",
            error,
            "```",
        ]

    lines += [
        "",
        "## Evidence",
        "",
        "- `agent.log`: execution decisions and observations.",
        "- `screenshots/`: captured browser states.",
        "- `video/`: Playwright recording when available.",
        "",
        "PASS requires all recorded acceptance criteria to pass "
        "and no execution error to occur.",
        "",
    ]

    (run_dir / "final_report.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    return run_status
