import json

SYSTEM_PROMPT = """You are a QA test planner. Return only a JSON object:
{"goal":"string","steps":[{"id":"string","action":"navigate|click|inspect","target_description":"string","expected_observation":"string"}]}.
Create 4-8 concise steps from the supplied user story and acceptance criteria. Never claim a test passed. Do not provide code, CSS/XPath selectors, or arbitrary browser commands."""


def generate_plan(client, model: str, issue: dict) -> dict:
    """Ask the LLM to turn issue acceptance criteria into a bounded test plan."""
    payload = {
        "issue_id": issue["id"],
        "title": issue["title"],
        "user_story": issue.get("user_story", ""),
        "acceptance_criteria": issue["acceptance_criteria"],
        "target_url": issue["target_url"],
    }
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(payload)},
        ],
        timeout=45,
    )
    plan = json.loads(response.choices[0].message.content)
    steps = plan.get("steps")
    if not isinstance(steps, list) or not 1 <= len(steps) <= 8:
        raise ValueError("Planner returned an invalid plan: expected 1-8 steps.")
    allowed = {"navigate", "click", "inspect"}
    for step in steps:
        if step.get("action") not in allowed or not step.get("target_description"):
            raise ValueError(f"Planner returned an unsupported/incomplete step: {step}")
    return plan
