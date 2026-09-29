from app.executor.context_management.context_rules import AGENT_CONTEXT_POLICY

class ContextPolicy:
    def get_allowed_sources(self,agent_name):
        allowed_list = AGENT_CONTEXT_POLICY[agent_name]["allowed"]
        return allowed_list

    def get_optional_sources(self,agent_name):
        optional_list = AGENT_CONTEXT_POLICY[agent_name]["optional"]
        return optional_list


