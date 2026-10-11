import time
import requests
import sys

import os
BASE_URL = os.getenv("BENCHMARK_URL", "http://localhost:8000/api/v1/chat")
HEALTH_URL = os.getenv("HEALTH_URL", "http://localhost:8000/api/v1/health")

QUERIES = [
    {
        "name": "Simple Greeting",
        "message": "Hello, who are you?",
    },
    {
        "name": "RAG Retrieval",
        "message": "What does Lenny say about finding your first 1000 users?",
    },
    {
        "name": "Writing Task",
        "message": "Write a short essay on product-led growth based on the podcast.",
    }
]

def run_benchmark(provider: str, model: str):
    print(f"\n{'='*50}")
    print(f"BENCHMARK: {provider.upper()} ({model})")
    print(f"{'='*50}")
    
    for q in QUERIES:
        print(f"\n--- Query: {q['name']} ---")
        start_time = time.time()
        
        try:
            resp = requests.post(BASE_URL, json={
                "message": q["message"],
                "provider": provider,
                "model": model,
                "conversation_id": None
            })
            end_time = time.time()
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"Total Client Time: {end_time - start_time:.2f}s")
                
                # Check for artifacts
                artifacts = data.get("artifacts", [])
                if artifacts:
                    print(f"Generated {len(artifacts)} artifact(s).")
                
            else:
                print(f"Error {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    print("Wait a moment for server to be ready...")
    time.sleep(2)
    # Check if server is up
    try:
        requests.get(HEALTH_URL)
    except:
        pass

    run_benchmark("local", "llama3:latest")
    run_benchmark("cloud", "openai/gpt-4o-mini")
