from pydantic import BaseModel, Field, ConfigDict
from typing import Literal



# With Pydantic, the class-level declarations:are how Pydantic discovers:
# "These are my model fields, and these are their validation rules."

class Route(BaseModel):
    model_config = ConfigDict(extra="forbid")
    route_id : str = Field(min_length = 1, description="Unique identifier for this execution step.")
    agent : str = Field(min_length = 1, description = "Identifier of the specialist agent responsible for this task.")
    task : str = Field(min_length=1, description = "Focused task description for the specialist agent")
    dependencies : list[str] = Field(default_factory = list) # "When no dependencies are supplied, call list() to create the default.
    # When to use default_fctory? - "Does this field need a default value, and is that default something that needs to be newly created for each instance?"
    # default_factory is about creating defaults, not about values changing from one Router call to another.
    is_final: bool = Field( default=False, description="Whether this route produces the final user-facing answer.")

class RouteDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    routes : list[Route]  = Field(min_length=1, description="Specialist execution routes required to fulfill the request." )# It tells Pydantic: routes must be a list, and every item in that list must be a valid Route object.
    execution_mode : Literal["dependency_aware"] = Field(description="Specifies whether execution mode is parallel or sequential")
    confidence : float = Field(ge= 0 , le=1,   description="Confidence that the proposed routing decision fulfills the user's request.")
    routing_reason : str = Field(min_length=1, description= "Concise reason for the routing decision.")

'''
# When you put them inside:
# you're moving them into ordinary Python initialization logic.
# So you're essentially saying: "When someone creates a Route, manually assign these attributes."
# hat's not how we want Pydantic's BaseModel to work.
class Route(BaseModel):
    def __init__(self):
        self.agent : str = Field(min_length = 1, description = "Identifier of the specialist agent responsible for this task.")
        self.task : str = Field(min_length=1, description = "Focused task description for the specialist agent")
        self.priority : int = Field(ge = 1)
        self.dependencies : list[str] = Field(default_factory = list)
'''


