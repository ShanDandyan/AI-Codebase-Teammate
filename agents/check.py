import json
import sqlite3

conn = sqlite3.connect("Codebase_teammate.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

REQ_ID = 28

print(f"\n================ AUDIT REPORT FOR REQUEST #{REQ_ID} ================\n")

# 1. Check Requests Table
cursor.execute("SELECT * FROM requests WHERE id = ?", (REQ_ID,))
req = cursor.fetchone()
if req:
    print("--- 1. REQUESTS TABLE ---")
    print(f"ID              : {req['id']}")
    print(f"Timestamp       : {req['timestamp']}")
    print(f"Question        : {req['question']}")
    print(f"Final Answer    :\n{req['final_answer'][:200]}...\n")
else:
    print(f"⚠️ Request #{REQ_ID} not found in requests table!\n")

# 2. Check Agent Decisions Table
print("--- 2. AGENT DECISIONS TABLE ---")
cursor.execute("SELECT * FROM agent_decisions WHERE request_id = ? ORDER BY id ASC", (REQ_ID,))
decisions = cursor.fetchall()
if decisions:
    for idx, d in enumerate(decisions, start=1):
        print(f"[{idx}] Agent     : {d['agent_name']} | Time: {d['timestamp']}")
        print(f"    Reasoning : {d['reasoning']}\n")
else:
    print("⚠️ No decision rows found.\n")

# 3. Check Tool Calls Table
print("--- 3. TOOL CALLS TABLE ---")
cursor.execute("SELECT * FROM tool_calls WHERE request_id = ? ORDER BY id ASC", (REQ_ID,))
calls = cursor.fetchall()
if calls:
    for idx, tc in enumerate(calls, start=1):
        print(f"[{idx}] Tool      : {tc['tool_name']} | Time: {tc['timestamp']}")
        print(f"    Input JSON: {tc['input']}")
        
        # Verify JSON deserialization
        try:
            parsed_input = json.loads(tc['input'])
            print(f"    Parsed Args: {parsed_input}")
        except Exception as e:
            print(f"    ⚠️ Input JSON Parsing Error: {e}")
            
        output_preview = tc["output"][:150].replace("\n", " ")
        print(f"    Output Text: {output_preview}...\n")
else:
    print("⚠️ No tool call rows found.\n")

conn.close()