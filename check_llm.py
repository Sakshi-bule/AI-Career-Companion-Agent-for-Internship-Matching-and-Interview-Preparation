"""Quick test of your Groq key and model, independent of the web app.

Run from the project folder:  python check_llm.py
"""
from src import extractor  # loads .env and the same settings the app uses
import os

from openai import OpenAI

key = (os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip().strip('"').strip("'")
if not key:
    raise SystemExit(f"No GROQ_API_KEY found. Create a .env file at {extractor.ENV_PATH}")

print(f"Key loaded: yes (starts with {key[:4]}..., length {len(key)})")
print(f"Base URL: {extractor.BASE_URL}")
print(f"Model: {extractor.MODEL_NAME}\n")

client = OpenAI(api_key=key, base_url=extractor.BASE_URL, timeout=30)

print("1) Models available to your key:")
try:
    names = sorted(m.id for m in client.models.list().data)
    for n in names:
        print("   -", n)
    if extractor.MODEL_NAME not in names:
        print(f"\n   WARNING: '{extractor.MODEL_NAME}' is not in the list. Set LLM_MODEL in .env to one of the names above.")
except Exception as exc:
    print("   FAILED:", exc)

print(f"\n2) Test call to '{extractor.MODEL_NAME}':")
try:
    r = client.chat.completions.create(
        model=extractor.MODEL_NAME,
        messages=[{"role": "user", "content": "Reply with the single word: OK"}],
    )
    print("   SUCCESS:", r.choices[0].message.content)
except Exception as exc:
    print("   FAILED:", exc)
    print("   401 = wrong key | 404 = wrong model name | 429 = rate limit, wait a minute")
