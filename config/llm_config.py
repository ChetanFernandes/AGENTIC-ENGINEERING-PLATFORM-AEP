import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.chat_models import init_chat_model
from portkey_ai import createHeaders,PORTKEY_GATEWAY_URL,Portkey

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

#llm_openai = ChatOpenAI(model="gpt-5-mini", api_key=OPENAI_API_KEY, use_responses_api=True, output_version="responses/v1",)
#llm_openai = ChatOpenAI(model="gpt-5-mini", api_key=OPENAI_API_KEY, use_responses_api=True, output_version="responses/v1", reasoning={"effort": "none"})

llm_openai_mini = ChatOpenAI(model="gpt-5-mini", api_key=OPENAI_API_KEY, use_responses_api=True, output_version="responses/v1",)



PORTKEY_API_KEY = os.getenv("PORTKEY_API")

metadata = {
               "_user" :    "aep",
               "environment": "production",
                "feature":     "aep"
}

portkey_headers = createHeaders(api_key = PORTKEY_API_KEY, metadata = metadata, config = "pc-retry-eee669")

llm_openai = ChatOpenAI(api_key = PORTKEY_API_KEY, base_url=PORTKEY_GATEWAY_URL, default_headers = portkey_headers,output_version="responses/v1")
















'''
from deepagents.middleware.summarization import compute_summarization_defaults

defaults = compute_summarization_defaults(llm_openai)

print(defaults)
'''


#llm_openai = ChatOpenAI(model = "gpt-5-mini", openai_api_key=OPENAI_API_KEY, max_input_tokens = 272000, max_output_tokens = 128000)
#print(llm_openai.profile)


#print(llm_openai.profile)


#OLLAMA_HOST = "https://semimechanistic-kraig-ideally.ngrok-free.dev"
#llm_ollama = ChatOllama(model ="Qwen2.5-Coder:3B",model_provider="ollama",base_url=OLLAMA_HOST, temperature=0.2, configurable_fields="any",reasoning = False )
#result = llm_ollama.invoke("What is capital of India")
#print(result)








