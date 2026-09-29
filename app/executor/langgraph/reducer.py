from app.schemas.agent_output_schema import AgentOutput

def merge(current_state_output: dict[str , AgentOutput] , update_state_output : dict[str , AgentOutput] ) -> dict[str , AgentOutput]:
    return {**current_state_output , **update_state_output} # ** means "unpack this dictionary into another dictionary."

def merge_dicts(existing: dict[str, str], new: dict[str, str]) -> dict[str, str]:
    return { **existing, **new}