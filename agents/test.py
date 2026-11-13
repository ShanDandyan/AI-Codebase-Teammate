import json
import httpx
from httpx_sse import connect_sse

url = "http://127.0.0.1:8000/ask/stream"
payload = {
    "question": "What files are in the ShanDandyan/DocuMind-AI repo, and what does the README.md say?"
}

print("--- STARTING STREAM CLIENT ---", flush=True)

with httpx.Client(timeout=60.0) as client:
    with connect_sse(client, "POST", url, json=payload) as event_source:
        for sse in event_source.iter_sse():
            event_data = json.loads(sse.data)
            print(f"\n[RECEIVED EVENT]: {event_data['event'].upper()}", flush=True)
            print(json.dumps(event_data, indent=2), flush=True)