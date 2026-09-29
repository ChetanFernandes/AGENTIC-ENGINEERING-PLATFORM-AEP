from deepagents.backends import StoreBackend
from langgraph.store.memory import InMemoryStore
from deepagents.backends.utils import create_file_data
from app.permession_management.permession_wrapper import PolicyWrapper
from pathlib import Path
from uuid import uuid4
from langgraph.store.postgres import PostgresStore
from config.database_config import DB_URI
from app.schemas.custom_schemas import ArtifactRecord
from app.artifacts_storage.artifcats_storage import ArtifactStorage
from app.schemas.agent_output_schema import AgentOutput
from logger.log import setup_logging
log = setup_logging()
import asyncio


class backend:

    def __init__(self, blob_storage):
        self.store_context = PostgresStore.from_conn_string(DB_URI)  # "Create a LangGraph Store that uses my PostgreSQL database."
        self.store = self.store_context.__enter__() # "Actually enter that connection and give me the Store object."
        self.store.setup()  # ensures the Store's PostgreSQL tables are initialized.
        self.artifact_storage = ArtifactStorage()
        self.blob_storage = blob_storage
        self.update_defaults()

    def update_defaults(self):
        # Check for memory, if present dont update
        namespace_memory = ("shared", "memory")
        key =  "/AGENTS.md"
        path = Path(r"app/executor/langgraph/AGENTS.md")
        item = self.store.get(namespace_memory,key)
        self.store.put(namespace_memory, "/AGENTS.md", create_file_data(path.read_text(encoding = 'utf-8')))
        ''' 
        if not item:
            self.store.put(namespace_memory, "/AGENTS.md", create_file_data(path.read_text(encoding = 'utf-8')))
        else:
            pass
        '''
        # check for Learnings
        key =  "/LEARNINGS.md"
        item = self.store.get(namespace_memory,key)
        if not item:
            self.store.put(namespace_memory, key , create_file_data("When working on repository tasks, verify the current git branch before making changes."))
        else:
            pass

        # check for skills
        namespace_skills = ("shared","skills")
        key = "/skills/SKILL.md"
        path = Path(r"skills/repository-analysis/SKILL.md")
        item = self.store.get(namespace_skills,key)
        if not item:
            self.store.put(namespace_skills , key, create_file_data(path.read_text(encoding='utf-8')))
        else:
            pass


    def store_backend_memory_shared(self):
        return StoreBackend(namespace = lambda _rt: ("shared", "memory"), store = self.store)

    def store_backend_memory_personal(self):
        return StoreBackend(namespace = lambda rt: ("users", rt.context.user_id,), store = self.store)

    def store_backend_skills_shared(self):
        return StoreBackend(namespace = lambda _rt: ("shared", "skills"), store = self.store)

    def store_agent_output(self,agent, user_id, agent_output):
        artifact_id = str(uuid4())
        storage_key = f"{agent}/{user_id}/{artifact_id}"

        #self.artifact_storage.local_save(storage_key,agent_output)
        self.artifact_storage.blob_save(storage_key,agent_output, self.blob_storage)

        artifact_record = ArtifactRecord(artifact_id = artifact_id , user_id = user_id, agent = agent, storage_key = storage_key)
        self.store_artifact_record_SQL(artifact_record)
        return artifact_record

    async def get_agent_output(self, user_id, artifact_id,):
        namespace = ("artifacts", user_id)
        key = artifact_id
        item  = await self.store.aget(namespace,key)
        if not item:
            return None
        try:
            artifact_record = item.value
        except Exception:
            artifact_record = item.value["content"]
        storage_key = artifact_record.get("storage_key",None)
        if not storage_key:
            return None
        
        #data = self.artifact_storage.get_local(storage_key)
        
        data = await asyncio.to_thread(self.artifact_storage.get_from_blob, storage_key, self.blob_storage)

        return AgentOutput.model_validate_json(data) # Convert to object AgentOutput


    def store_artifact_record_SQL(self,artifact_record):
        namespace = ("artifacts", artifact_record.user_id)
        key = artifact_record.artifact_id
        self.store.put(namespace, key, artifact_record.model_dump()) # Pydantic object → Python dictionary

    def return_store(self):
        return self.store

    def policy_wrapper(self):
        memory_policy_wrapper = PolicyWrapper(self.store_backend_memory_shared(), deny_prefix=[ "/memories/shared/AGENTS.md"])
        skills_policy_wrapper = PolicyWrapper(self.store_backend_skills_shared(), deny_prefix=[ "/skills/repository-analysis"])

        return memory_policy_wrapper, skills_policy_wrapper

    def read_agent_learning(self):
        namespace = ("shared", "memory")
        key = "/LEARNINGS.md"
        item = self.store.get(namespace, key)
        data = item.value["content"]
        if data:
            return data
        else:
            return None

    def write_learning(self,updated_learning):
        namespace = ("shared", "memory")
        key = "/LEARNINGS.md"
        self.store.put(namespace, key,create_file_data(updated_learning))

    def read_user_personal_memory(self,user_id):
        namespace = ("users", user_id)
        key = f"/{user_id}_USER_MEMORY.md"
        item = self.store.get(namespace,key)
        if not item:
            return None
        data = item.value["content"]
        if data:
            return data
        else:
            return None

    def close(self):
        self.store_context.__exit__(None, None, None)
        
    

if __name__ =="__main__":
    back = backend()
    print(back.read_learning())


'''
def store_agent_output(self,agent, user_id, agent_output):
        # namespace = ("artifacts",user_id)
        # key = artifact_id
        # self.store.put(namespace, key, agent_output)

def get_agent_output(self, user_id, artifact_id,):
    
    # namespace = ("artifacts",user_id)
    # key = artifact_id
    # self.store.get(namespace, key, agent_output)
'''

    
        






        
                




