from deepagents import create_deep_agent
from llm_config import llm_openai
from langchain.tools import ToolRuntime, tool
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend, FilesystemBackend
from langgraph.store.memory import InMemoryStore
from langchain.tools import tool
from typing_extensions import TypedDict
from deepagents.backends import StoreBackend
import inspect



store = InMemoryStore()

'''
@tool
def get_store_data(runtime:ToolRuntime): #"Inject the runtime for me, and its context has this shape."
    """Get teh skill data from store"""
    assert runtime.store is not None
    print(runtime.context["user_role"])
    skill = runtime.store.get(namespace=("engineering",),  key="filesystem")
    print(skill)
'''

from deepagents.backends import StoreBackend

sb = StoreBackend(
    namespace=lambda rt: ("dumm",),
    store=store
)

print(sb._namespace)
print(callable(sb._namespace))




agent = create_deep_agent(model = llm_openai, skills = ["/skills/"], 
                          backend = CompositeBackend(default=StateBackend(),
                                                     routes = {"/skills/":StoreBackend(namespace= ("dumm",), store = store)}),
)

result = agent.invoke(
               {"messages":[{"role":"user" , "content" : "Look up for skills"}]},
            )

print(result)
