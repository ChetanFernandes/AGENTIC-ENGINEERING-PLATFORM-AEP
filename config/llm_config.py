import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain.chat_models import init_chat_model


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

llm_openai = ChatOpenAI(model="gpt-6-luna", api_key=OPENAI_API_KEY, use_responses_api=True, output_version="responses/v1",)


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








