from pydantic import BaseModel , Field
from app.schemas.custom_schemas import AgentOutput
from typing import Any

class Context(BaseModel):
    context: dict[str , Any] = Field(default_factory=dict)