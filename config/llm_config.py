import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.chat_models import init_chat_model
from portkey_ai import createHeaders,PORTKEY_GATEWAY_URL,Portkey

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

#llm_openai = ChatOpenAI(model="gpt-5-mini", api_key=OPENAI_API_KEY, use_responses_api=True, output_version="responses/v1",)
#llm_openai = ChatOpenAI(model="gpt-5-mini", api_key=OPENAI_API_KEY, use_responses_api=True, output_version="responses/v1", reasoning={"effort": "none"})


class llm_call:
 
    def __init__(self):
        self.port_api_key = os.getenv("PORTKEY_API")
        self.portkey_gateway_url = PORTKEY_GATEWAY_URL

    def port_key(self, user_id:str, execution_id:str):

        portkey_metadata = {"_user": str(user_id), "execution_id": str(execution_id)}

        portkey_headers = createHeaders(api_key =  self.port_api_key, metadata = portkey_metadata, config = "pc-retry-eee669")

        llm_open_ai = ChatOpenAI(api_key = self.port_api_key, base_url = self.portkey_gateway_url, 
                                 default_headers = portkey_headers, output_version="responses/v1")

        print("model_name:", llm_open_ai.model_name)
        print("profile:", llm_open_ai.profile)
        print("base_url:", llm_open_ai.openai_api_base)
        
        return llm_open_ai

llm_openai_luna = ChatOpenAI(model="gpt-6-Luna", api_key=OPENAI_API_KEY, use_responses_api=True, output_version="responses/v1",)




#print(llm_openai.profile)


#OLLAMA_HOST = "https://semimechanistic-kraig-ideally.ngrok-free.dev"
#llm_ollama = ChatOllama(model ="Qwen2.5-Coder:3B",model_provider="ollama",base_url=OLLAMA_HOST, temperature=0.2, configurable_fields="any",reasoning = False )
#result = llm_ollama.invoke("What is capital of India")
#print(result)








