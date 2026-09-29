from portkey_ai import createHeaders,PORTKEY_GATEWAY_URL,Portkey
from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser


load_dotenv()
PORTKEY_API_KEY = os.getenv("PORTKEY_API")

model_1 = "@groq/openai/gpt-oss-20b"
model_2 = "@openai/gpt-5-luna"


metadata = {
              "_user":    "langchain-demo",
               "environment": "notebook",
                "feature":     "langchain-integration"
}

portkey_headers = createHeaders(api_key = PORTKEY_API_KEY, metadata = metadata, config = "pc-retry-eee669")

llm = ChatOpenAI(api_key = PORTKEY_API_KEY, base_url=PORTKEY_GATEWAY_URL, default_headers = portkey_headers)

lb_questions = [
    "What is a Kubernetes Ingress resource?",
    "How does OSPF differ from BGP?",
    "What is Intel FPGA acceleration?",
    "Explain Kubernetes HPA.",
    "What is a VLAN trunk?",
    "How does Kubernetes etcd work?",
]

for i, q in enumerate(lb_questions):

    # withot chain and messages
    response = llm.invoke(q)
    print("\n")
    print("%s -> %s",i, q)
    print("Answer", response.content)
    print("\n")


    # chain based with messages and template
    prompt = ChatPromptTemplate.from_messages([('system', "You are an Enterprise IT expert. Be concise."), 
                                        ('human',"{question}")])

    chain = prompt | llm | StrOutputParser()

    response = chain.invoke({"question" : q})
    print("\n")
    print("%s -> %s",i, q)
    print("Answer", response)
    print("\n")


   # chain based with direct messages and without prompt template
    response = chain.invoke([SystemMessage(content  = "You are an Enterprise IT expert. Be concise."),
                             HumanMessage(content = q)])


    print("\n")
    print("%s -> %s",i, q)
    print("Answer", response)
    print("\n")









