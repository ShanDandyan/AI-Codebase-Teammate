import sqlite3
import json
from datetime import datetime
# Establish Connection
conn=sqlite3.connect("Codebase_teammate.db")
c=conn.cursor()

#Prerequisite to make sure foreign key activated
c.execute("PRAGMA foreign_keys = ON")

# Create all tables required
c.execute("""
    CREATE TABLE IF NOT EXISTS requests(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question text,
    final_answer text,
    timestamp text,
    confidence_score real
    )""")
c.execute("""
    CREATE TABLE IF NOT EXISTS tool_calls(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id integer,
    tool_name text,
    input text,
    output text ,
    timestamp text,
    FOREIGN KEY (request_id) REFERENCES requests(id)

    )""")
c.execute("""
    CREATE TABLE IF NOT EXISTS agent_decisions(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id integer,
    timestamp text,
    agent_name text,
    reasoning text,
    FOREIGN KEY (request_id) REFERENCES requests(id)
    )""")
c.execute(
    """CREATE TABLE IF NOT EXISTS eval_results(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id integer,
    score integer,
    expected_answer text,
    notes text,
    FOREIGN KEY (request_id) REFERENCES requests(id)
    )"""
) 
conn.commit()
conn.close()

# Functions for each table
def create_request(question):
    conn=sqlite3.connect("Codebase_teammate.db")
    c=conn.cursor()
    value=(question,None,None,None)
    c.execute("INSERT INTO requests (question,final_answer,timestamp,confidence_score)VALUES(?,?,?,?)",value)
    conn.commit()
    conn.close()
    return c.lastrowid
def log_tool_call(request_id,tool_name,tool_input,tool_output):
    conn=sqlite3.connect("Codebase_teammate.db")
    c=conn.cursor()
    value=(request_id,tool_name,tool_input,tool_output,None)
    c.execute("INSERT INTO tool_calls (request_id,tool_name,input,output,timestamp) VALUES(?,?,?,?,?)",value)
    conn.commit()
    conn.close()
def log_agent_decision(request_id,agent_name,reasoning):
    conn=sqlite3.connect("Codebase_teammate.db")
    c=conn.cursor()
    now = datetime.now().isoformat()
    value=(request_id,now,agent_name,reasoning)
    c.execute("INSERT INTO agent_decisions(request_id,timestamp,agent_name,reasoning) VALUES(?,?,?,?)",value)
    conn.commit()
    conn.close()
def log_eval_results(request_id,expected_answer,score,notes):
    conn=sqlite3.connect("Codebase_teammate.db")
    c=conn.cursor()
    value=(request_id,score,expected_answer,notes)
    c.execute("INSERT INTO eval_results(request_id,score,expected_answer,notes) VALUES(?,?,?,?)",value)
    conn.commit()
    conn.close()  

def create_request(question: str) -> int:
    """Inserts a new user request with the current timestamp and returns its request_id."""
    conn=sqlite3.connect("Codebase_teammate.db")
    c=conn.cursor()
    now = datetime.now().isoformat()
    c.execute(
        """
        INSERT INTO requests (question, final_answer, timestamp)
        VALUES (?, '', ?)
        """,
        (question, now),
    )
    request_id = c.lastrowid
    conn.commit()
    conn.close()
    return request_id


def complete_request(
    request_id: int, final_answer: str, confidence_score: float = None
):
    """Updates the request row with the final answer, status, and optional confidence score."""
    conn=sqlite3.connect("Codebase_teammate.db")
    c=conn.cursor()
    c.execute(
        """
        UPDATE requests
        SET final_answer = ?, confidence_score = ?
        WHERE id = ?
        """,
        (final_answer, confidence_score, request_id),
    )
    conn.commit()
    conn.close()


def log_agent_decision(request_id: int, agent_name: str, reasoning: str):
    """Logs a decision step into the agent_decisions table."""
    conn=sqlite3.connect("Codebase_teammate.db")
    c=conn.cursor()
    now = datetime.now().isoformat()
    c.execute(
        """
        INSERT INTO agent_decisions (request_id, agent_name, reasoning, timestamp)
        VALUES (?, ?, ?, ?)
        """,
        (request_id, agent_name, reasoning, now),
    )
    conn.commit()
    conn.close()


def log_tool_call(request_id: int, tool_name: str, input_args: dict, output_text: str):
    """Logs a row into tool_calls using input and output columns."""
    conn=sqlite3.connect("Codebase_teammate.db")
    c=conn.cursor()
    now = datetime.now().isoformat()

    # Convert tool args dictionary to JSON string for the 'input' column
    input_json = json.dumps(input_args) if isinstance(input_args, dict) else str(input_args)

    c.execute(
        """
        INSERT INTO tool_calls (request_id, tool_name, input, output, timestamp)
        VALUES (?, ?, ?, ?, ?)
        """,
        (request_id, tool_name, input_json, output_text, now),
    )
    conn.commit()
    conn.close()

def get_full_request_details(request_id: int) -> dict:
    """Fetches a request along with all its agent decisions and tool calls."""
    conn=sqlite3.connect("Codebase_teammate.db")
    c=conn.cursor()

    # Query request
    c.execute("SELECT * FROM requests WHERE id = ?", (request_id,))
    req = c.fetchone()
    if not req:
        conn.close()
        return None

    # Query decisions
    c.execute(
        "SELECT agent_name, reasoning, timestamp FROM agent_decisions WHERE request_id = ? ORDER BY id ASC",
        (request_id,),
    )
    decisions = [dict(d) for d in c.fetchall()]

    # Query tool calls
    c.execute(
        "SELECT tool_name, input, output, timestamp FROM tool_calls WHERE request_id = ? ORDER BY id ASC",
        (request_id,),
    )
    tool_calls = [dict(t) for t in c.fetchall()]

    conn.close()

    return {
        "request": dict(req),
        "decisions": decisions,
        "tool_calls": tool_calls,
    }


if __name__ == "__main__":
    # Testing for proper join      
    request_id = create_request("How does the authorization system work")
    log_tool_call(request_id, "read file", "auth.py", "<data>")
    log_agent_decision(request_id, "agent_1", "some reasoning here")
    log_eval_results(request_id, "<answer here>", 65, "<notes>")

    complete_request(request_id, "Test final answer completed successfully.")
    print("Schema self-test execution completed.")