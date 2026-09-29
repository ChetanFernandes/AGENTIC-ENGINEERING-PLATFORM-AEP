from portkey_ai import Portkey, createHeaders, PORTKEY_GATEWAY_URL
from dotenv import load_dotenv
load_dotenv()
import os
import time

PORTKEY_API_KEY = os.getenv("PORTKEY_API")
print(f"\nPortkey Gateway : {PORTKEY_GATEWAY_URL}")

model_1 = "@groq/openai/gpt-oss-20b"
model_2 = "@openai/gpt-6-luna"

portkey = Portkey(api_key = PORTKEY_API_KEY)

def section(title):
    print(f"\n{'='*62}")
    print(f"  {title}")
    print(f"{'='*62}")

def show(q, answer, ms, label=""):
    bar = chr(9472) * 62
    print(f"\n{bar}")
    print(f"Question: {q}")
    print(f"Answer: {answer[:260]}{'...' if len(answer) > 260 else ''}")
    note = f" | {label}" if label else ""
    print(f"⏱  {ms/1000:.4f}seconds{note}")
    print(bar)

section("EXPERIMENT 1 — Route Through the Gateway")



# ------------EXPERIMENT 1 — Route Through the Gateway---------------------

def port_key(question):
    start_time = time.time()
    response = portkey.chat.completions.create(model= model_1,
                                                                    messages=[
                                                                        {"role": "system", "content": "You are a helpful assistant."},
                                                                        {"role": "user", "content": question}
                                                                    ],
    max_completion_tokens=512)
    answer = response.choices[0].message.content
    show(question, answer , ms = time.time() - start_time , label = "routed via Portkey gateway_using_groq")

if __name__ == "__main__":
    questions = [
            "What is AI and gen ai ?",
            "What is coffee and black coffee?",
        ]
    for q in questions:
        port_key(question = q)

# ------------EXPERIMENT 2 — Metadata & Observability---------------------
import uuid

section("EXPERIMENT 2 — Metadata & Observability")
session = str(uuid.uuid4())[:8]

def port_key_expt_2():
    scenarios = [
            ("alice", "enterprise-rag",   "What is Kubernetes RBAC?"),
            ("bob",   "docs-chatbot",     "How does BGP path selection work?"),
            ("carol", "support-bot",      "What is SRIOV virtualization?"),
            ("alice", "enterprise-rag",   "Explain Kubernetes NetworkPolicy"),   # same user, diff Q
        ]
    
    for user, feature, question in scenarios:
        start_time = time.time()
        response = portkey.with_options(
                metadata= {
                    "_user" : user,
                    "session_id" : session,
                    "feature": feature,
                    "environment": "development"

                }
                ).chat.completions.create(model= model_1,
                                        messages=[
                                            {"role": "system", "content": "You are a helpful assistant."},
                                            {"role": "user", "content": question}
                                        ],
        
                                        max_completion_tokens=512)

        
        answer = response.choices[0].message.content[:120]
        print(f"\n👤 {user:8s} | 🔧 {feature:18s}")
        show(question, answer , ms = time.time() - start_time , label = "routed via Portkey gateway_using_groq")
        
if __name__ == "__main__": 
        port_key_expt_2()
