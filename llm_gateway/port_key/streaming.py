from portkey_ai import createHeaders,PORTKEY_GATEWAY_URL,Portkey
from dotenv import load_dotenv
import os



load_dotenv()
PORTKEY_API_KEY = os.getenv("PORTKEY_API")

model_1 = "@groq/openai/gpt-oss-20b"
model_2 = "@openai/gpt-5-luna"


portkey_streaming = Portkey(api_key=PORTKEY_API_KEY, config="pc-retry-eee669")

print("stream=True works with any Portkey config — logging, fallbacks, and retries still apply.\n")

print("Streaming response: ", end="", flush=True)


stream = portkey_streaming.chat.completions.create(
    model=model_1,
    messages=[{"role": "user", "content": "Explain what an LLM gateway does in exactly 3 bullet points."}],
    stream=True
)

for chunk in stream:
    delta = chunk.choices[0].delta.content
    if delta:
        print(delta, end="", flush=True)


print("\n✅ Full request is still logged in Portkey dashboard — streaming doesn't lose observability.")
print("   Add stream=True to any existing call. All gateway features still apply.")