from portkey_ai import Portkey, createHeaders, PORTKEY_GATEWAY_URL
from dotenv import load_dotenv
load_dotenv()
import os
import time

PORTKEY_API_KEY = os.getenv("PORTKEY_API")


model_1 = "@groq/openai/gpt-oss-20b"
model_2 = "@openai/gpt-6-luna"



portkey_cached = Portkey(api_key=PORTKEY_API_KEY, config="pc-retry-eee669")


# Use a short, precise question with temperature=0 to maximise cache-key stability
q = "Define Kubernetes ConfigMap in one sentence."
call_params = dict(
    model=model_1,
    messages=[{"role": "user", "content": q}],
    max_completion_tokens=512)


print("--- CALL 1: Cache MISS — Portkey forwards to Groq ---")
t0 = time.time()
r1 = portkey_cached.chat.completions.create(**call_params)
t1 = (time.time() - t0) * 1000
ans1 = r1.choices[0].message.content.strip()
print(f"Answer  : {ans1[:200]}")
print(f"Latency : {t1/1000:.3f}s | Cost: normal token price")