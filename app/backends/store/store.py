from deepagents.backends import StoreBackend
#from langgraph.store.memory import InMemoryStore
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
from langchain.tools import tool
from langchain.tools import tool, ToolRuntime
import os
log = setup_logging()
import asyncio



class backend:

    def __init__(self, blob_storage):
        self.store_context = PostgresStore.from_conn_string(DB_URI)  # "Create a LangGraph Store that uses my PostgreSQL database."
        self.store = self.store_context.__enter__() # "Actually enter that connection and give me the Store object."
        self.store.setup()  # ensures the Store's PostgreSQL tables are initialized.
        self.artifact_storage = ArtifactStorage()
        self.blob_storage = blob_storage

    @classmethod # means the method belongs to the class rather than a specific object.
    async def create(cls,blob_storage): #cls refers to the class itself, such as backend.
        instance = cls(blob_storage) # is equivalent to instance = backend(blob_storge)
        await instance.update_defaults()
        return instance
    

    async def update_defaults(self):
        namespace_memory = ("main_agent", "main_agent_skill")
        key =  "/AGENTS.md"
        path = Path(r"app/executor/langgraph/AGENTS.md")
        item = await self.store.aget(namespace_memory,key)
        #log.info('Agent_md_data_item:%s',item)
        data = item.value.get("content","") if item else ""
        #log.info('Agent_md_data:%s',data)
        if not data:
            await self.store.aput(namespace_memory, "/AGENTS.md", create_file_data(path.read_text(encoding = 'utf-8')))
     
      
        namespace_memory = ("main_agent", "main_agent_learning")
        key =  "/SKILL.md"
        item = await self.store.aget(namespace_memory,key)
        data = item.value.get("content","") if item else ""
        if not data:
            await self.store.aput(namespace_memory, key , create_file_data(""))
        else:
            pass

        #---------------------------------------------

        # check for skills
        namespace_skills = ("sub_agent","sub_agent_skill")
        key = "/SKILL.md"
        path = Path(r"skills/repository-analysis/SKILL.md")
        item = await self.store.aget(namespace_skills,key)
        #log.info('SKILL_MD_item:%s',item)
        data = item.value.get("content","") if item else ""
        #log.info('SKILL_MD:%s',data)
        if not data:
            await self.store.aput(namespace_skills , key, create_file_data(path.read_text(encoding='utf-8')))
        else:
            pass

    # -------------------------------------------------------------------------------------
    def store_backend_main_agent_skill(self):
        return StoreBackend(namespace = lambda _rt: ("main_agent", "main_agent_skill"), store = self.store)

    def store_backend_main_agent_learning(self):
        return StoreBackend(namespace = lambda _rt: ("main_agent", "main_agent_learning"), store = self.store)

    def store_backend_sub_agent_skills(self):
        return StoreBackend(namespace = lambda _rt: ("sub_agent", "sub_agent_skill"), store = self.store)

    def policy_wrapper(self):

        main_agent_skill_policy_wrapper = PolicyWrapper(self.store_backend_main_agent_skill(), deny_prefix = ["/AGENTS.md"])

        main_agent_learning_policy_wrapper = PolicyWrapper(self.store_backend_main_agent_learning(),)

        subagent_skills_policy_wrapper = PolicyWrapper(self.store_backend_sub_agent_skills(), deny_prefix = ["/SKILL.md"])

        return main_agent_skill_policy_wrapper, main_agent_learning_policy_wrapper, subagent_skills_policy_wrapper

    # --------------------------------------------------------------------------------------------------------------------------

    def store_backend_memory_personal(self):
        return StoreBackend(namespace = lambda rt: ("users", rt.context.user_id,), store = self.store)

    #--------------------Storing Agent Output----------------------------------------------------------------------------------------------

    async def store_agent_output(self,agent, user_id, agent_output, execution_id):
        artifact_id = str(uuid4())
        storage_key = f"{user_id}/{execution_id}/{agent}/{artifact_id}"

        #self.artifact_storage.local_save(storage_key,agent_output)
        self.artifact_storage.blob_save(storage_key, agent_output, self.blob_storage)

        artifact_record = ArtifactRecord(artifact_id = artifact_id , user_id = user_id, agent = agent, storage_key = storage_key, execution_id=execution_id)
        await self.store_artifact_record_SQL(artifact_record)
        return artifact_record


    async def store_artifact_record_SQL(self,artifact_record):
        namespace = ("artifacts", artifact_record.user_id)
        key = artifact_record.artifact_id
        await self.store.aput(namespace, key, artifact_record.model_dump()) # Pydantic object → Python dictionary

    #-------------------------Storing Agent Output---------------------------------------------------------------------------------------

    
    async def get_agent_output(self, user_id, artifact_id,):
        namespace = ("artifacts", user_id)
        key = artifact_id
        item  = await self.store.aget(namespace,key)

        print("ARTIFACT LOOKUP")
        print("namespace:", namespace)
        print("key:", key)
        print("item:", item)

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

        #print("1. Before get_from_blob")
        #print("storage_key:", storage_key)
        #print("blob_storage:", self.blob_storage)
        
        data = await asyncio.to_thread(self.artifact_storage.get_from_blob, storage_key, self.blob_storage)

        #print("2. After get_from_blob")
        #print("data type:", type(data))
        #print("data length:", len(data) if data else None)

        #print("3. Before model_validate_json")


        return AgentOutput.model_validate_json(data) # Convert to object AgentOutput


    def return_store(self):
        return self.store


    #-----------------------------Read and write agent learning memory-----------------------------------------------------

    async def read_agent_learning(self):
        """ Used to read the existing learning from store """
        namespace = ("main_agent", "main_agent_learning")
        key = "/SKILL.md"
        item = await self.store.aget(namespace, key)
        data = item.value.get("content")
        if data:
            return data
        else:
            return None

    async def write_learning(self,updated_learning):
        """ Used to update new learning in the store"""
        namespace = ("main_agent", "main_agent_learning")
        key = "/SKILL.md"
        await self.store.aput(namespace, key, create_file_data(updated_learning))

#----------------------------Read user personal memory------------------------------------------------------

    async def read_user_personal_memory(self,user_id):
        '''This is not requuired'''
        namespace = ("users", user_id)
        key = f"/USER_MEMORY.md"
        item = await self.store.aget(namespace,key)
        if item:
            data = item.value.get("content","")
        else:
            return None
        if data:
            return data
        else:
            return None

# ----------------------Writing user memory ----------------------------------
    async def write_user_personal_memory(self,user_id:str, agent_learning:str):
        """Store important user information for future conversations."""
        namespace = ("users", user_id)

        key = f"/USER_MEMORY.md"

        # Read existing memory
        existing_memory = await self.store.aget(namespace,key)
        log.info("User_Existing_Memory:\n%s",existing_memory)
        # Item(namespace=['users', 'Chetan'], key='/USER_MEMORY.md', 
        # value={'content': 'Test', 'encoding': 'utf-8', 'created_at': '2026-10-11T15:54:10.989603+00:00', 'modified_at': '2026-10-11T15:54:10.989603+00:00'}, 
        # created_at='2026-10-11T21:24:10.990085+05:30', updated_at='2026-10-11T21:24:10.990085+05:30')"}

        existing_content = ""

        if existing_memory and isinstance(existing_memory.value, dict):
            existing_content = existing_memory.value.get("content", "")

        # Clean new memory
        new_memory = agent_learning.strip()

        if not new_memory:
            log.info("No memory provided.")
            return "No memory provided."


        # Duplicate check
        if new_memory.lower() in existing_content.lower():
            log.info("%s memory already exists. Skipping.", user_id)
            return "Memory already exists. Skipping duplicate."
  
        # Append new memory
        if existing_content.strip():
            updated_content = (
                existing_content.rstrip()
                + "\n\n"
                + new_memory
            )
 
        else:
            updated_content = new_memory

        await self.store.aput(namespace, key, create_file_data(updated_content))

        log.info("%s memory updated", user_id)

        return "Memory stored successfully."

    def get_write_memory_tool(self):

        @tool
        async def write_memory(memory: str, runtime: ToolRuntime):
            """Store important information about the user for future conversations."""

            user_id = runtime.context.user_id

            return await self.write_user_personal_memory(user_id=user_id, agent_learning=memory)

        return write_memory

    # ----------------------close----------------------------------


        
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

    
    



        
                




