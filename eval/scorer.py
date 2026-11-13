import re

def normalize_text(text: str) -> str:
    # Convert Unicode hyphens/dashes (\u2010-\u2015) to standard ASCII hyphen
    return re.sub(r'[\u2010-\u2015]', '-', (text or "")).lower()

def score_eval_run(
    final_answer: str,
    actual_tools: list[str],
    expected_tools: list[str],
    required_facts: list,
    forbidden_facts: list[str] = None,
) -> tuple[int, str]:
    notes = []
    forbidden_facts = forbidden_facts or []

    # 1. Tool Check (40 pts) — supports either single tool name or list of valid tool alternatives
    missing_tools = []
    for req_tool in expected_tools:
        if isinstance(req_tool, (list, tuple)):
            if not any(t in actual_tools for t in req_tool):
                missing_tools.append(f"Any of {req_tool}")
        else:
            if req_tool not in actual_tools:
                missing_tools.append(req_tool)

    if not missing_tools:
        tool_score = 40
    else:
        matched = len(expected_tools) - len(missing_tools)
        tool_score = int((matched / len(expected_tools)) * 40) if expected_tools else 0
        notes.append(f"Missing tools: {missing_tools}")

    # 2. Fact Check (60 pts)
    answer_norm = normalize_text(final_answer)
    matched_facts = 0
    missing_facts = []

    for fact in required_facts:
        if isinstance(fact, (list, tuple)):
            if any(normalize_text(str(alt)) in answer_norm for alt in fact):
                matched_facts += 1
            else:
                missing_facts.append(f"Any of {fact}")
        else:
            if normalize_text(str(fact)) in answer_norm:
                matched_facts += 1
            else:
                missing_facts.append(fact)

    hallucinated = [f for f in forbidden_facts if normalize_text(f) in answer_norm]

    if hallucinated:
        fact_score = 0
        notes.append(f"Hallucinated: {hallucinated}")
    elif required_facts:
        fact_score = int((matched_facts / len(required_facts)) * 60)
        if missing_facts:
            notes.append(f"Missing facts: {missing_facts}")
    else:
        fact_score = 60

    return tool_score + fact_score, "; ".join(notes) if notes else "Passed."
