from portkey_ai import Portkey, createHeaders, PORTKEY_GATEWAY_URL
from dotenv import load_dotenv
load_dotenv()
import os
import time

PORTKEY_API_KEY = os.getenv("PORTKEY_API")


model_1 = "@groq/openai/gpt-oss-20b"
model_2 = "@openai/gpt-6-luna"



portkey_lb = Portkey(api_key=PORTKEY_API_KEY, config="pc-retry-eee669")



lb_questions = [
    "What is a Kubernetes Ingress resource?",
    "How does OSPF differ from BGP?",
    "What is Intel FPGA acceleration?",
    "Explain Kubernetes HPA.",
    "What is a VLAN trunk?",
    "How does Kubernetes etcd work?",
]

print("Sending 6 requests. Expect ~4 on large model (70b), ~2 on small model (8b) (probabilistic).\n")

for i, q in enumerate(lb_questions, 1):
    try:
        t0 = time.time()
        r = portkey_lb.chat.completions.create(
            messages=[{"role": "user", "content": q}]
        )
        ms = (time.time() - t0) * 1000
        print(f"Req {i} [{ms:.0f}ms]: {q}")
        print(f"         {r.choices[0].message.content[:120]}...")
    except Exception as e:
        print(f"Req {i}: ERROR — {e}")

print("\n✅ Check Portkey Logs to see which provider served each request")
print("   Set weight=0 to pause a target without removing it from the config")