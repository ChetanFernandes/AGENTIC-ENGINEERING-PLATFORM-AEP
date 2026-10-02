from pydantic import BaseModel, Field
from typing import  Any

class AgentOutput(BaseModel):
    status: str
    summary: str|None = None
    result: str | None  = None
    errors: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)



    # str | None = what values are allowed
    # So both are valid:
    # artifact_id = "artifact-123"   # string
    # artifact_id = None             # no artifact
    # = None . This is the default value
    # If you don't provide artifact_id, Python automatically sets it to None.
    # For example:
    # AgentOutput(
            #status="completed",
            #summary="Done"
        #)

    # Because we didn't provide artifact_id, it becomes:

#artifact_id = None



