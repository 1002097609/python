import os, sys, json, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r"D:\claude_demo\demo2\demo")

from backend.database import engine  # trigger load_dotenv
import httpx

API_KEY = os.getenv("ANTHROPIC_AUTH_TOKEN", "")
BASE_URL = os.getenv("ANTHROPIC_BASE_URL", "https://api.longcat.chat/anthropic")
MODEL = os.getenv("ANTHROPIC_MODEL", "LongCat-2.0-Preview")

# Try different auth headers
headers_options = [
    {"name": "x-api-key", "headers": {"x-api-key": API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"}},
    {"name": "Authorization Bearer", "headers": {"Authorization": f"Bearer {API_KEY}", "anthropic-version": "2023-06-01", "content-type": "application/json"}},
    {"name": "x-api-key (no anthropic-version)", "headers": {"x-api-key": API_KEY, "content-type": "application/json"}},
]

payload = {
    "model": MODEL,
    "max_tokens": 512,
    "messages": [{"role": "user", "content": "你好，请用一句话介绍你自己"}],
}

for opt in headers_options:
    print(f"\n--- Testing: {opt['name']} ---")
    try:
        with httpx.Client(timeout=15) as client:
            resp = client.post(f"{BASE_URL}/v1/messages", headers=opt["headers"], json=payload)
            print(f"Status: {resp.status_code}")
            body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text
            print(f"Response: {json.dumps(body, ensure_ascii=False)[:500]}")
            if resp.status_code == 200:
                print(f"\nSUCCESS with: {opt['name']}")
                break
    except Exception as e:
        print(f"Error: {e}")
