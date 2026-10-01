from pydantic import BaseModel, Field
from typing import Literal
'''

#RouteDecision
│
├── routes[]
│   ├── agent
│   ├── task
│   ├── priority
│   └── dependencies[]
│
├── execution_mode
├── confidence
└── routing_reason

routes = [
    Route(
        agent="security",
        task="Identify security vulnerabilities.",
        priority=1,
        dependencies=[]
    ),
    Route(
        agent="performance",
        task="Identify performance bottlenecks.",
        priority=1,
        dependencies=[]
    )
]

'''
# With Pydantic, the class-level declarations:are how Pydantic discovers:
# "These are my model fields, and these are their validation rules."

class Route(BaseModel):
    route_id : str = Field(min_length = 1)
    agent : str = Field(min_length = 1, description = "Identifier of the specialist agent responsible for this task.")
    task : str = Field(min_length=1, description = "Focused task description for the specialist agent")
    priority : int = Field(ge = 1 , le = 3)
    dependencies : list[str] = Field(default_factory = list) # "When no dependencies are supplied, call list() to create the default.
    # When to use default_fctory? - "Does this field need a default value, and is that default something that needs to be newly created for each instance?"
    # default_factory is about creating defaults, not about values changing from one Router call to another.
    is_final: bool = Field( default=False, description="Whether this route produces the final user-facing answer.")

class RouteDecision(BaseModel):
    routes : list[Route] # It tells Pydantic: routes must be a list, and every item in that list must be a valid Route object.
    execution_mode : Literal["dependency_aware execution"] = Field(description="Specifies whether execution mode is parallel or sequential")
    confidence : float = Field(ge= 0 , le=1)
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


