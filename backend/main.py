import os
import sys
import json
import inspect
import sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import agents.simple_agent as agent_module

DB_PATH = os.path.join(ROOT_DIR, "Codebase_teammate.db")

app = FastAPI(
    title="AI Codebase Teammate API",
    version="1.0.0",
    description="Backend service for repo analysis, streaming trajectories, and SQLite logging.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QuestionRequest(BaseModel):
    question: str


async def invoke_agent(question: str) -> dict:
    for fn_name in ("run_agent", "ask_agent", "query_agent", "run", "main"):
        fn = getattr(agent_module, fn_name, None)
        if callable(fn):
            res = fn(question)
            if inspect.isawaitable(res):
                res = await res
            if isinstance(res, dict):
                return res
            if isinstance(res, tuple) and len(res) >= 2:
                return {"final_answer": str(res[0]), "tools_used": list(res[1])}
            return {"final_answer": str(res), "tools_used": []}
    raise RuntimeError("No runnable entry function found in agents/simple_agent.py")


@app.get("/", response_class=HTMLResponse)
def root():
    ui_path = os.path.join(ROOT_DIR, "frontend", "index.html")
    if os.path.exists(ui_path):
        with open(ui_path, "r", encoding="utf-8") as f:
            return f.read()
    return HTMLResponse("<h3>frontend/index.html not found</h3>", status_code=404)


@app.post("/ask")
async def ask_agent(payload: QuestionRequest):
    try:
        result = await invoke_agent(payload.question)
        answer = result.get("final_answer", "")
        tools = result.get("tools_used", [])
        return {"question": payload.question, "final_answer": answer, "tools_used": tools}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/ask/stream")
async def ask_agent_stream(payload: QuestionRequest):
    async def event_stream():
        try:
            stream_fn = getattr(agent_module, "run_agent_stream", None)
            if callable(stream_fn):
                async for event in stream_fn(payload.question):
                    if isinstance(event, str):
                        yield f"data: {json.dumps({'type': 'token', 'content': event})}\n\n"
                        continue

                    if not isinstance(event, dict):
                        continue

                    ev_type = str(event.get("type") or event.get("event") or event.get("node") or "")

                    if ev_type in ("tool_result", "decision", "start"):
                        yield f"data: {json.dumps({'type': 'trace', 'detail': event})}\n\n"
                    elif "tool_start" in ev_type or "on_tool_start" in ev_type:
                        tool = event.get("tool") or event.get("name") or "tool"
                        yield f"data: {json.dumps({'type': 'tool_start', 'tool': tool, 'input': event.get('input', '')})}\n\n"
                    elif "tool_end" in ev_type or "on_tool_end" in ev_type or ev_type == "tools":
                        tool = event.get("tool") or event.get("name") or "mcp_tool"
                        yield f"data: {json.dumps({'type': 'tool_end', 'tool': tool})}\n\n"
                    else:
                        text = (
                            event.get("content")
                            or event.get("answer")
                            or event.get("final_answer")
                            or event.get("text")
                            or event.get("output")
                        )
                        if isinstance(text, str) and text.strip():
                            yield f"data: {json.dumps({'type': 'token', 'content': text})}\n\n"
                        else:
                            yield f"data: {json.dumps({'type': 'trace', 'detail': event})}\n\n"
            else:
                result = await invoke_agent(payload.question)
                for tool in result.get("tools_used", []):
                    yield f"data: {json.dumps({'type': 'tool_end', 'tool': str(tool)})}\n\n"
                yield f"data: {json.dumps({'type': 'token', 'content': result.get('final_answer', '')})}\n\n"

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'content': str(exc)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/requests/{request_id}")
def read_request(request_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM requests WHERE id = ?", (request_id,))
    req = c.fetchone()
    if not req:
        conn.close()
        raise HTTPException(status_code=404, detail="Request not found")

    c.execute("SELECT * FROM tool_calls WHERE request_id = ? ORDER BY id ASC", (request_id,))
    tools = [dict(r) for r in c.fetchall()]
    conn.close()
    return {"request": dict(req), "tool_calls": tools}


@app.get("/eval/latest")
def get_latest_eval(limit: int = 24):
    if not os.path.exists(DB_PATH):
        return {"average_score": 0, "total": 0, "results": []}
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(
        """
        SELECT e.id, r.question, e.score, e.notes
        FROM eval_results e
        JOIN requests r ON e.request_id = r.id
        ORDER BY e.id DESC LIMIT ?
        """,
        (limit,),
    )
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    avg = round(sum(r["score"] for r in rows) / len(rows), 1) if rows else 0
    return {"average_score": avg, "total": len(rows), "results": rows}