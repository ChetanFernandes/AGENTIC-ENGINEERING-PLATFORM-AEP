from abc import ABC, abstractmethod
from pathlib import Path
from app.artifacts_storage.azure_blob import BlobStorage

class Artifacts_Storage(ABC):

    @abstractmethod
    def local_save(self,storage_key,data):
        pass

    @abstractmethod
    def blob_save(self,storage_key,data,blob_storage:BlobStorage):
        pass

    @abstractmethod
    def get_local(self,storage_key):
        pass

    @abstractmethod
    def get_from_blob(self,storage_key,blob_storage:BlobStorage):
        pass

class ArtifactStorage(Artifacts_Storage):
    def __init__(self):
        path = Path("agent_output")
        path.mkdir(parents=True, exist_ok=True)
        self.path = path

    def local_save(self,storage_key,data):
        data = data.model_dump_json()
        file_path = self.path / storage_key           # / is joining path not division
        file_path.parent.mkdir(parents = True, exist_ok = True)
        file_path.write_text(data, encoding="utf-8")  # write_text() is the Path equivalent of opening with "w" and calling write().
        #with open(file_path,"w",encoding="utf-8") as file:
            #file.write(data)

    def blob_save(self,storage_key,data,blob_storage:BlobStorage):
        data = data.model_dump_json()
        blob_storage.save_file(storage_key,data)
       
    def get_local(self,storage_key):
        file_path = self.path / storage_key
        return file_path.read_text(encoding = "utf-8")
        #with open(file_path,'r',encoding="utf-8") as data:
            #return data.read()

    def get_from_blob(self,storage_key,blob_storage:BlobStorage):
        print("C: entered get_from_blob")
        return blob_storage.read_file(storage_key)
   
   




    
        

