from app.schemas.agent_output_schema import AgentOutput
from typing import Any

def merge(current_state_output: dict[str , AgentOutput] , update_state_output : dict[str , AgentOutput] ) -> dict[str , AgentOutput]:
    return {**current_state_output , **update_state_output} # ** means "unpack this dictionary into another dictionary."

def merge_dicts(existing: dict[str, str], new: dict[str, str]) -> dict[str, str]:
    return { **existing, **new}

RESET_KEY = "__reset__"

RESET_VALUE = "__RESET__"

def merge_or_reset(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:

    if new.get(RESET_KEY) == RESET_VALUE:
        return {}

    return {**old, **new}