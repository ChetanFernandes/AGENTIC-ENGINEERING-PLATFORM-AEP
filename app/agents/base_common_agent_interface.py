from abc import ABC, abstractmethod
from app.schemas.agent_output_schema import AgentOutput

class AgentInterface(ABC):
    @abstractmethod
    def execute(self,task:str) -> AgentOutput:
        pass


    

    

