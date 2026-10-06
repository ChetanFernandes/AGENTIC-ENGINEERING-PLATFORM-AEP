from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    user_name:str = Field(min_length = 1)
    thread_id:str = Field(min_length = 1)
    question:str = Field(min_length = 1)

class ResumeRequest(BaseModel):
    user_name: str
    thread_id: str
    decision: str
