from langchain.agents.middleware import PIIMatch, PIIMiddleware


def pii_middleware():
    return PIIMiddleware(pii_type = "email",strategy = "mask", apply_to_input = True, apply_to_output = True, apply_to_tool_results = False)