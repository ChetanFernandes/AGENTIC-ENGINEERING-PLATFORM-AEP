from azure.identity import DefaultAzureCredential
from config.azure_config import AZURE_ACCOUNT_NAME, AZURE_CONTAINER
from azure.storage import blob
from io import BytesIO
from azure.storage.blob import BlobServiceClient
from logger.log import setup_logging
log = setup_logging()

class BlobStorage:
    """Read and saves the files to Azure Blob"""
    def __init__(self):
        log.info("Intialiing Azure blob")
        try:
            self.account_name  = AZURE_ACCOUNT_NAME
            self.container  = AZURE_CONTAINER
            self.credential =  DefaultAzureCredential()
            
            self.service = BlobServiceClient(
                        account_url=(
                        f"https://"
                        f"{self.account_name}"
                        ".blob.core.windows.net"),
                    credential=self.credential
                )
            self.container_client = (self.service.get_container_client(container = self.container))
            
            log.info("DataLakeReader initialized successfully")

        except Exception:
            log.exception("Blob initlization failed")

    def save_file(self,path:str, data):
        blob_client = self.container_client.get_blob_client(path)
        blob_client.upload_blob(data, overwrite=True)
        log.info("Agent_output_saved_successfully to:%s",path)


    def read_file(self,path:str) -> str:
        """ Download file to memeory"""
        try:
            print(f">>> Reading blob: {path}")
            blob_client = self.container_client.get_blob_client(path)
            data = blob_client.download_blob(timeout=30).readall()
            return data.decode("utf-8") # converts bytes → string using UTF-8 encoding.
            #return BytesIO(data)
        
        except Exception:
            log.exception(f"Reading the file failed for path {path}")
            raise

  
        

