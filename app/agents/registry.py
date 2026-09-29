from app.agents.security_agent import SecurityAgent , RepositoryAgent

AGENT_REGISTRY = {
                  "repository" :    RepositoryAgent,
                  "architecture" :    "agent_class",
                  "security" :    SecurityAgent,
                  "performance" : "agent_class",
                  "code_engineering" : "agent_class",
                  "code_review": "agent_class",
                   "testing": "agent_class",
                   "Jira/workflow": "agent_class",
                   "optimization": "agent_class",
                   "refactoring": "agent_class",
                   }


def get_agent(agent_name:str):
    if agent_name in AGENT_REGISTRY:
        agent_class = AGENT_REGISTRY[agent_name]
        agent_object = agent_class()
        return agent_object

    else:
        raise ValueError(f"Invalid agent_name {agent_name} called by Router")

