import urllib.request
import json
import time

def test_ollama():
    url = "http://localhost:11434/api/chat"
    
    # Prompt instructing no thinking
    payload = {
        "model": "qwen3.5:9b-q4_K_M",
        "messages": [
            {
                "role": "system", 
                "content": "Tu es un traducteur médical. Traduis directement en français. Ne fais aucune réflexion, n'utilise aucune balise <think>."
            },
            {
                "role": "user", 
                "content": "Standard physiotherapy programs are beneficial for chronic low back pain."
            }
        ],
        "stream": False,
        "think": False,
        "options": {
            "temperature": 0.0,
            "num_predict": 100
        }
    }
    
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    
    print("Sending request to Ollama...")
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=120.0) as response:
            res_data = json.loads(response.read().decode())
            duration = time.perf_counter() - start
            print(f"Success in {duration:.2f}s!")
            print("Response:", json.dumps(res_data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Failed in {time.perf_counter() - start:.2f}s: {e}")

if __name__ == "__main__":
    test_ollama()
