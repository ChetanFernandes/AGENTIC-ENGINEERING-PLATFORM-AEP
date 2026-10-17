from pydantic import BaseModel , Field
from typing import Any

class Context(BaseModel):
    context: dict[str , Any] = Field(default_factory=dict)