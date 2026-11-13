import asyncio
import json
import os
import sys

from dotenv import load_dotenv

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from database.schema import (
    complete_request,
    create_request,
    log_agent_decision,
    log_tool_call,
)
from langchain_core.messages import SystemMessage
from langchain_groq import ChatGroq
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

load_dotenv()

SERVER_PATH = os.path.abspath(
    os.path.join(PROJECT_ROOT, "mcp_server", "server.py")
)
SYSTEM_PROMPT = SystemMessage(
    content=(
        "You are an AI Codebase Teammate. You have access to three tools: 'list_files', 'read_file', and 'get_commit_history'.\n"
        "NEVER call any other tools like 'search', 'web_search', or external search engines.\n"
        "To inspect a repository:\n"
        "1. Call list_files(repo_owner, repo_name) to see repository contents.\n"
        "2. Call read_file(repo_owner, repo_name, file_path) to read file contents.\n"
        "3. Call get_commit_history(repo_owner, repo_name, max_commits) to view recent commits."
    )
)



async def run_agent_stream(question: str):
    request_id = create_request(question)
    yield {"event": "start", "request_id": request_id, "question": question}

    try:
        client = MultiServerMCPClient(
            {
                "codebase": {
                    "transport": "stdio",
                    "command": sys.executable,
                    "args": [SERVER_PATH],
                }
            }
        )
        tools = await client.get_tools()

        llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)
        llm_with_tools = llm.bind_tools(tools)

        async def agent_node(state: MessagesState):
            messages = [SYSTEM_PROMPT] + state["messages"]
            response = await llm_with_tools.ainvoke(messages)
            return {"messages": [response]}

        builder = StateGraph(MessagesState)
        builder.add_node("agent", agent_node)
        builder.add_node("tools", ToolNode(tools))

        builder.add_edge(START, "agent")
        builder.add_conditional_edges("agent", tools_condition)
        builder.add_edge("tools", "agent")

        graph = builder.compile()

        pending_tool_calls = {}
        final_answer = ""

        async for update in graph.astream(
            {"messages": [("user", question)]}, stream_mode="updates"
        ):
            if "agent" in update:
                agent_msg = update["agent"]["messages"][-1]

                if hasattr(agent_msg, "tool_calls") and agent_msg.tool_calls:
                    for call in agent_msg.tool_calls:
                        call_id = call.get("id")
                        tool_name = call.get("name")
                        tool_args = call.get("args", {})

                        reasoning = f"Decided to call '{tool_name}' with parameters: {tool_args}"

                        log_agent_decision(
                            request_id=request_id,
                            agent_name="ReAct_Agent",
                            reasoning=reasoning,
                        )

                        pending_tool_calls[call_id] = {
                            "tool_name": tool_name,
                            "input_args": tool_args,
                        }

                        yield {
                            "event": "decision",
                            "tool_name": tool_name,
                            "input_args": tool_args,
                            "reasoning": reasoning,
                        }
                else:
                    final_answer = agent_msg.content

            elif "tools" in update:
                tool_messages = update["tools"]["messages"]
                for tool_msg in tool_messages:
                    call_id = getattr(tool_msg, "tool_call_id", None)
                    content = tool_msg.content

                    if (
                        isinstance(content, list)
                        and len(content) > 0
                        and isinstance(content[0], dict)
                    ):
                        output_text = content[0].get("text", str(content))
                    else:
                        output_text = str(content)

                    tool_info = pending_tool_calls.pop(call_id, {})
                    tool_name = tool_info.get("tool_name", "unknown_tool")
                    input_args = tool_info.get("input_args", {})

                    log_tool_call(
                        request_id=request_id,
                        tool_name=tool_name,
                        input_args=input_args,
                        output_text=output_text,
                    )

                    yield {
                        "event": "tool_result",
                        "tool_name": tool_name,
                        "output": output_text,
                    }

        complete_request(request_id, final_answer)

        yield {
            "event": "complete",
            "request_id": request_id,
            "final_answer": final_answer,
        }

    except Exception as e:
        yield {"event": "error", "error": str(e)}


async def run_agent(question: str) -> dict:
    final_result = {}
    async for event in run_agent_stream(question):
        if event["event"] == "complete":
            final_result = {
                "request_id": event["request_id"],
                "question": question,
                "final_answer": event["final_answer"],
            }
        elif event["event"] == "error":
            raise RuntimeError(event["error"])
    return final_result