
# Filssystem backend
from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend
from deepagents.backends import StateBackend, StoreBackend
from langgraph.checkpoint.memory import MemorySaver
from pathlib import Path
from llm_config import llm_openai, llm_ollama

checkpointer = MemorySaver()

path_local = r"D:\Agentic Engineering Platform — Project Plan\AEP"

backend = FilesystemBackend(root_dir = path_local, virtual_mode=True) 

#backend.upload_files(
    #[("/skills/langgraph-docs/SKILL.md", skill_content.encode("utf-8"))]


agent = create_deep_agent(llm_openai, 
                          backend = backend , 
                          skills = ["/skills"], 
                          interrupt_on = {"write_file": True, "read_file": True, "edit_file": True},
                          checkpointer = checkpointer)

result = agent.invoke({'messages' : [{"role":"user" , "content": "Read the content and past only lastline"}]},
                        config = {"configurable" : {"thread_id":"12345"}})

print(result["messages"][-1].content)

#----------------------------------SatateBackend------------------------------------


# state backend
from langgraph.checkpoint.memory import MemorySaver
from deepagents.backends.utils import create_file_data

checkpointer = MemorySaver()
backend = StateBackend()

path = Path(r"skills\repository-analysis\SKILL.md")

skills_files = {"/skills/repository-analysis/SKILL.md" : create_file_data(path.read_text(encoding='utf-8'))}

agent = create_deep_agent(llm_openai,backend = backend, skills = ["/skills"],  checkpointer = checkpointer)

result = agent.invoke( {
                        'messages' : [{"role":"user" , "content": "Read the content and past only lastline"}], 
                        "files": skills_files
                       },
                        config = {"configurable" : {"thread_id":"12345"}}
                     )



#-------------------------------------Storebackend-------------------------

from urllib.request import urlopen
from deepagents import create_deep_agent
from deepagents.backends import StoreBackend
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()

backend = StoreBackend(
    namespace=lambda _rt: ("filesystem",),
    store=store,
)

path = Path(r"skills\repository-analysis\SKILL.md")

backend.upload_files([("/skills/repository-analysis/SKILL.md", path.read_text(encoding='utf-8'))])

agent = create_deep_agent(
    model="google_genai:gemini-3.6-flash",
    backend=backend,
    store=store,
    skills=["/skills/"],
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "What is langgraph?"}]},
    config={"configurable": {"thread_id": "12345"}},
)


#-------------------------------------------Dynamicnamespace--------------------------
SKILLS_BY_ROLE = { 
                  "engineering" : ["/skills"]
                  }

agent = create_deep_agent(model = llm_openai, skills = SKILLS_BY_ROLE.get("user_role",{}))

result = agent.invoke(
               {"messages":[{"role":"user" , "content" : "what is langgraph"}]},
                 context = {"user_role":"engineering"}
            )

print(agent.get_state)

