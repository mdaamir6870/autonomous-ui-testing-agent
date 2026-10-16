import json
import pytest
from src.issue_reader import load_issue


def test_load_issue_accepts_rfqa(tmp_path):
    issue = {
        "id": "QA-TEST", "title": "Example", "status": "Ready for QA",
        "target_url": "https://example.com",
        "acceptance_criteria": [{"id": "AC1", "text": "Example criterion"}],
    }
    path = tmp_path / "issue.json"
    path.write_text(json.dumps(issue), encoding="utf-8")
    assert load_issue(str(path))["id"] == "QA-TEST"


def test_load_issue_rejects_non_rfqa(tmp_path):
    issue = {
        "id": "QA-TEST", "title": "Example", "status": "In Progress",
        "target_url": "https://example.com",
        "acceptance_criteria": [{"id": "AC1", "text": "Example criterion"}],
    }
    path = tmp_path / "issue.json"
    path.write_text(json.dumps(issue), encoding="utf-8")
    with pytest.raises(ValueError, match="Ready for QA"):
        load_issue(str(path))
