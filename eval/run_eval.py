# eval/run_eval.py

import asyncio
import os
import sqlite3
import sys
import time

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from agents.simple_agent import run_agent
def log_eval_result(
    request_id: int, expected_answer: str, eval_score: int, notes: str
):
    """Logs evaluation results to SQLite using the 'score' column."""
    conn = sqlite3.connect("Codebase_teammate.db")
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO eval_results (request_id, expected_answer, score, notes)
        VALUES (?, ?, ?, ?)
    """,
        (request_id, expected_answer, eval_score, notes),
    )
    conn.commit()
    conn.close()
from eval.questions import EVAL_QUESTIONS
from eval.scorer import score_eval_run

DB_PATH = os.path.join(PROJECT_ROOT, "Codebase_teammate.db")


def get_actual_tools(request_id: int) -> list[str]:
    """Retrieves tool names executed for a specific request ID."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT tool_name FROM tool_calls WHERE request_id = ?", (request_id,)
    )
    tools = [row[0] for row in c.fetchall()]
    conn.close()
    return tools


async def main():
    print("=" * 60)
    print(f"STARTING EVALUATION RUN ({len(EVAL_QUESTIONS)} QUESTIONS)")
    print("=" * 60)

    results = []

    for q in EVAL_QUESTIONS:
        q_id = q["id"]
        question = q["question"]
        expected_tools = q["expected_tools"]
        required_facts = q["required_facts"]

        print(f"\n[Q{q_id}/24] Running: '{question}'...")

        try:
            # 1. Run Agent
            agent_output = await run_agent(question)
            request_id = agent_output["request_id"]
            final_answer = agent_output["final_answer"]

            # 2. Fetch Actual Tools Called
            actual_tools = get_actual_tools(request_id)

            # 3. Compute Score
            score, notes = score_eval_run(
            final_answer=final_answer,
            actual_tools=actual_tools,
            expected_tools=expected_tools,
            required_facts=required_facts,
            forbidden_facts=q.get("forbidden_facts", []),
        )

            # 4. Log to DB
            expected_str = f"Tools: {expected_tools} | Facts: {required_facts}"
            log_eval_result(
                request_id=request_id,
                expected_answer=expected_str,
                eval_score=score,
                notes=notes,
            )

            results.append({
                "id": q_id,
                "question": question,
                "score": score,
                "notes": notes,
                "tools_called": actual_tools,
            })

            print(f"      Score: {score}/100 | Notes: {notes}")

        except Exception as e:
            print(f"      ERROR running Q{q_id}: {str(e)}")
            results.append({
                "id": q_id,
                "question": question,
                "score": 0,
                "notes": f"Execution error: {str(e)}",
                "tools_called": [],
            })

        # Sleep briefly to respect API rate limits
        time.sleep(2)

    # --- EVALUATION SUMMARY ---
    total_score = sum(r["score"] for r in results)
    avg_score = total_score / len(results)

    print("\n" + "=" * 60)
    print(f"EVALUATION COMPLETE | AVERAGE SCORE: {avg_score:.1f}/100")
    print("=" * 60)

    failed_questions = [r for r in results if r["score"] < 100]

    if failed_questions:
        print("\nQUESTIONS SCORING BELOW 100:")
        for f in failed_questions:
            print(
                f"- [Q{f['id']}] Score: {f['score']}/100 | Notes: {f['notes']}"
            )
    else:
        print("\nALL QUESTIONS PASSED WITH A PERFECT 100 SCORE!")


if __name__ == "__main__":
    asyncio.run(main())