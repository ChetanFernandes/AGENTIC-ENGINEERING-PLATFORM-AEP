import pytest
from app.agents.schemas import AgentOutput
from app.executor.langgraph.reducer import merge_agent_outputs

def merge_agent_outputs(current_state_output: dict[str, AgentOutput], update_state_output: dict[str, AgentOutput]) -> dict[str, AgentOutput]:
    return {**current_state_output, **update_state_output}

def test_merge_agent_outputs():

    # Define dummy output
    repository_output = AgentOutput(result = "repository_completed")
    security_output = AgentOutput(result = "security_completed")

    # make output in its standard format Annoted[dict[str,Any]]

    current = { "repository" : repository_output }
    update = {"security": security_output}

    merged = merge_agent_outputs(current , update)

    print(merged)

    assert "repository" in merged
    assert "security" in merged


    assert merged["repository"] == repository_output
    assert merged["security"] == security_output






