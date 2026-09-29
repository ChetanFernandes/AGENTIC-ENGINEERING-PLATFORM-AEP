from app.agents.base_common_agent_interface import AgentInterface
from app.schemas.custom_schemas import AgentOutput

class SecurityAgent(AgentInterface):

    def execute(self,task:str) -> AgentOutput:
        return AgentOutput(result = "Security is good ")

class RepositoryAgent(AgentInterface):
    def execute(self,task:str) -> AgentOutput:
        return AgentOutput(result = "rep is good ")


if __name__ == "__main__":
    security = SecurityAgent()
    result = security.execute("Find the vulrabilites in security")
    print(result.result)