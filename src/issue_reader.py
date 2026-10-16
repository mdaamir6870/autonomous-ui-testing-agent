import json
from pathlib import Path


def load_issue(path: str = "mock_issue.json") -> dict:
    """Load a local mock issue and ensure it is ready for QA."""
    issue_path = Path(path)
    if not issue_path.exists():
        raise FileNotFoundError(f"Mock issue not found: {issue_path.resolve()}")

    issue = json.loads(issue_path.read_text(encoding="utf-8"))
    required = {"id", "title", "status", "target_url", "acceptance_criteria"}
    missing = sorted(required - issue.keys())
    if missing:
        raise ValueError(f"Mock issue is missing fields: {missing}")
    if issue["status"].strip().lower() != "ready for qa":
        raise ValueError(
            f"Issue {issue['id']} has status {issue['status']!r}; "
            "expected 'Ready for QA'."
        )
    if not isinstance(issue["acceptance_criteria"], list) or not issue["acceptance_criteria"]:
        raise ValueError("Issue must contain at least one acceptance criterion.")
    return issue
