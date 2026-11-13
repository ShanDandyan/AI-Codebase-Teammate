# AI Codebase Teammate

An autonomous, tool-augmented AI repository analyst built with **LangGraph**, **FastMCP**, **FastAPI**, and **SQLite**, featuring real-time Server-Sent Events (SSE) trajectory observability and a hardened 24-question evaluation harness (**95% accuracy**).

---

## Architecture Overview

```text
┌─────────────────────────┐      SSE Stream (/ask/stream)      ┌──────────────────────────┐
│   Observability UI      │ ◄───────────────────────────────── │     FastAPI Backend      │
│  (frontend/index.html)  │ ─────────────────────────────────► │    (backend/main.py)     │
└─────────────────────────┘         POST /ask/stream           └────────────┬─────────────┘
                                                                            │
                                                                            ▼
┌─────────────────────────┐       SQLite Persistence           ┌──────────────────────────┐
│  Codebase_teammate.db   │ ◄───────────────────────────────── │  LangGraph + FastMCP     │
│  • requests             │                                    │  (agents/simple_agent.py)│
│  • tool_calls           │                                    └────────────┬─────────────┘
│  • eval_results         │                                                 │
└─────────────────────────┘                                                 ▼
                                                               ┌──────────────────────────┐
                                                               │    GitHub MCP Tools      │
                                                               │  • list_files            │
                                                               │  • read_file / search    │
                                                               └──────────────────────────┘
AI Codebase Teamate/
├── agents/
│   └── simple_agent.py       # LangGraph + FastMCP agent and event streamer
├── backend/
│   └── main.py               # FastAPI server, SSE endpoints, SQLite read routes
├── frontend/
│   └── index.html            # Split-pane live chat & trajectory telemetry UI
├── database/
│   └── schema.py             # SQLite schema definitions
├── Codebase_teammate.db      # Persistent request, tool call, and eval logs
├── Dockerfile                # Multi-step Python 3.11 container definition
├── .dockerignore             # Build context exclusions
├── requirements.txt          # Python dependencies
└── .env                      # API keys (GROQ_API_KEY, GITHUB_TOKEN)
