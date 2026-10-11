from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
import os

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

embeddings = OpenAIEmbeddings(model="text-embedding-3-small",api_key=OPENAI_API_KEY)

#vector = embeddings.embed_query("What repository was I working on previously?")

#print("Embedding dimensions:", len(vector))
#print("First 5 values:", vector[:5])