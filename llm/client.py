import os, requests
from dotenv import load_dotenv

load_dotenv()
API_KEY  = os.getenv("UPSTAGE_API_KEY")
API_BASE = (os.getenv("UPSTAGE_API_BASE") or "").rstrip("/")
MODEL    = os.getenv("UPSTAGE_CHAT_MODEL", "solar-1-mini-chat")

def hello():
    if not API_KEY or not API_BASE:
        raise RuntimeError("Set UPSTAGE_API_KEY and UPSTAGE_API_BASE in .env")
    url = f"{API_BASE}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "한 문장으로 짧게 인사해줘"}]
    }
    r = requests.post(url, json=data, headers=headers, timeout=30)
    r.raise_for_status()
    j = r.json()
    return j["choices"][0]["message"]["content"]
