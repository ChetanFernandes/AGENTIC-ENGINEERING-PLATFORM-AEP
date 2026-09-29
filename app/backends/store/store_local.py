from deepagents.backends import StoreBackend
from langgraph.store.memory import InMemoryStore
from deepagents.backends.utils import create_file_data
from permession_management.permession_wrapper import PolicyWrapper
from pathlib import Path
from uuid import uuid4
from langgraph.store.postgres import PostgresStore
from database_config import DB_URI
from logger.log import setup_logging
log = setup_logging()


class backend:

    def __init__(self):
        self.store = InMemoryStore()
        self.namespace_memory = ("shared", "memory")
        self.store.put(self.namespace_memory, "/AGENTS.md", create_file_data("""## Response style
                                                                                                - Keep responses concise
                                                                                    """
                                                                                    ),
                                        )

        self.store.put(self.namespace_memory,"/LEARNINGS.md", create_file_data(""))

        self.namespace_skills = ("shared","skills")
        path = Path(r"skills/repository-analysis/SKILL.md")
        self.store.put(self.namespace_skills , "/skills/SKILL.md", create_file_data(path.read_text(encoding='utf-8')))



    def store_backend_memory_shared(self):
        return StoreBackend(namespace = lambda _rt: ("shared", "memory"), store = self.store)

    def store_backend_memory_personal(self):
        return StoreBackend(namespace = lambda rt: ("users", rt.context.user_id,), store = self.store)

    def store_backend_skills_shared(self):
        return StoreBackend(namespace = lambda _rt: ("shared", "skills"), store = self.store)

    def store_agent_output(self,agent_output,user_id):
        namespace = ("artifacts",user_id)
        artifact_id = str(uuid4())
        key = artifact_id
        self.store.put(namespace, key, agent_output)
        return artifact_id

    def get_agent_output(self,artifact_id,user_id):
        namespace = ("artifacts",user_id)
        item = self.store.get(namespace, artifact_id)
        if item:
            log.info(f"Data shared by store -> {item.value}")
            return item.value

        return None

    def return_store(self):
        return self.store

    def policy_wrapper(self):
        memory_policy_wrapper = PolicyWrapper(self.store_backend_memory_shared(), deny_prefix=[ "/memories/shared/AGENTS.md"])
        skills_policy_wrapper = PolicyWrapper(self.store_backend_skills_shared(), deny_prefix=[ "/skills/repository-analysis"])

        return memory_policy_wrapper, skills_policy_wrapper

    def read_learning(self):
            namespace = ("shared", "memory")
            key = "/LEARNINGS.md"
            item = self.store.get(namespace, key)
            if item:
                log.info(f"Data shared by store -> {item.value['content']}")
                return item.value['content']
            else:
                return None

    def write_learning(self,updated_learning):
        namespace = ("shared", "memory")
        key = "/LEARNINGS.md"
        self.store.put(namespace, key,create_file_data(updated_learning))

    

if __name__ =="__main__":
    back = backend()
    print(back.read_learning())





    
        






        
                




