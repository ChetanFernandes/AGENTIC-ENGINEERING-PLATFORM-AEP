from portkey_ai import Portkey, createHeaders, PORTKEY_GATEWAY_URL
from dotenv import load_dotenv
load_dotenv()
import os
import time

PORTKEY_API_KEY = os.getenv("PORTKEY_API")


model_1 = "@groq1/openai/gpt-oss-20b"
model_2 = "@openai/gpt-6-luna"

#--------------------Retry --------------------------
'''
retry_config = {
    "retry": {
                "attempts": 3,
                    "on_status_codes": [429, 500, 502, 503, 504]
              }
}


portkey_retry = Portkey(api_key=PORTKEY_API_KEY, config= "pc-retry-eee669")


print("Config: 3 retry attempts on [429, 500, 502, 503, 504]")
print("Retries fire automatically on failure — transparent to your code\n")


try:
    t0 = time.time()
    r = portkey_retry.chat.completions.create(
        model=model_1,
        messages=[{"role": "user", "content": "What is a AI?"}]
    )
    ms = (time.time() - t0) * 1000
    print(f"✅ Succeeded in {ms:.0f}ms")
    print(f"   {r.choices[0].message.content[:300]}")
    print("\nRetry sequence if Groq had failed:")
    print("  Attempt 1 → 429 → wait 1s → Attempt 2 → 429 → wait 2s → Attempt 3")
    print("  Your code only sees the final success or the last failure")
except Exception as e:
    print(f"❌ All attempts failed: {e}")
'''


#--------------------Timeout --------------------------

''' 
timeout_config = {"request_timeout": 1000}   # 10 seconds in ms

portkey_timeout = Portkey(api_key=PORTKEY_API_KEY, config= "pc-retry-eee669")


print("Timeout: 10,00ms (1 seconds). Portkey returns HTTP 408 if exceeded.\n")

try:
    t0 = time.time()
    r = portkey_timeout.chat.completions.create(
        model=model_1,
        messages=[{"role": "user", "content": "Explain Kubernetes networking in 2 sentences."}]
    )
    ms = (time.time() - t0) * 1000
    print(f"✅ Response in {ms/1000:.0f}ms (within 1s timeout)")
    print(f"   {r.choices[0].message.content}")
except Exception as e:
    print(f"⏱  Timed out: {e}")
    print("   Portkey issued a 408. Pair with fallback to auto-switch providers on timeout.")
'''

#--------------------Fallbacks --------------------------


portkey_forced = Portkey(api_key=PORTKEY_API_KEY, config= "pc-retry-eee669")

try:
    t0 = time.time()
    r = portkey_forced.chat.completions.create(
        messages=[{"role": "user", "content": "What is gen ai?"}]
    )
    ms = (time.time() - t0) * 1000
    print(f"✅ Got a response in {ms:.0f}ms despite the bad primary key!")
    print(f"   {r.choices[0].message.content[:250]}")
    print("\n→ Check Portkey Logs: attempt 1 shows FAILED (401), attempt 2 shows SUCCEEDED")
    print("   The fallback fired automatically — app code never saw the error.")
except Exception as e:
    print(f"❌ Both targets failed: {e}")