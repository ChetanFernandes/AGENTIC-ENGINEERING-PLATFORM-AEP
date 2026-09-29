from pydantic import BaseModel , Field

class ResourceSchema(BaseModel):
    type:str = Field(default = "repository")
    url:str = Field(min_length=1)
