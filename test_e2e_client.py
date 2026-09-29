import json
import requests
import sys

API_URL = "http://127.0.0.1:8000/api/v1/chat/stream"

def run_e2e_test():
    print(f"[Start] Initiating E2E Test against: {API_URL}\n")
    
    headers = {
        "Content-Type": "application/json",
        "X-User-Role": "citizen" # Injected as requested for Supabase logging
    }

    # Perfectly matching the ChatRequest Pydantic Schema
    payload = {
        "session_id": "e2e_test_session_99",
        "input_type": "text",
        "data": "How is resistance to cold conditions tested for current-carrying hoses?",
        "source_lang": "en"
    }

    print("[Info] Payload:")
    print(json.dumps(payload, indent=2))
    print("\n[Connecting] Connecting to stream...\n")

    try:
        # Open a streaming connection to the FastAPI server
        with requests.post(API_URL, json=payload, headers=headers, stream=True) as response:
            
            # Handle standard HTTP Errors (422 Unprocessable Entity, 500 Internal Error, etc.)
            if response.status_code != 200:
                print(f"[Error] HTTP Error {response.status_code}")
                print(f"Raw Response: {response.text}")
                sys.exit(1)
            
            print("[Connected] Stream Connected. Receiving events:\n")
            
            # Iterate over the raw byte lines of the SSE stream
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith("event: "):
                        print(f"[{decoded_line.split('event: ')[1].upper()}]", end=" ")
                    elif decoded_line.startswith("data: "):
                        # Parse the data payload if it's JSON
                        data_str = decoded_line.split("data: ")[1]
                        try:
                            data_json = json.loads(data_str)
                            if "text" in data_json:
                                print(f"-> {data_json['text']}", flush=True)
                            elif "citations" in data_json:
                                print(f"-> Citations: {data_json['citations']}", flush=True)
                            else:
                                print(f"-> {data_json}", flush=True)
                        except json.JSONDecodeError:
                            print(f"-> {data_str}", flush=True)
            
            print("\n\n[Success] Stream completed successfully.")

    except requests.exceptions.ConnectionError:
        print(f"[Error] Connection Error: Is the FastAPI server running on {API_URL}?")

if __name__ == "__main__":
    run_e2e_test()
