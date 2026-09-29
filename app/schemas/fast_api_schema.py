from pydantic import BaseModel, Field

class PayloadData(BaseModel):
    user_name:str = Field(min_length = 1)
    thread_id:str = Field(min_length = 1)
    question:str = Field(min_length = 1)
