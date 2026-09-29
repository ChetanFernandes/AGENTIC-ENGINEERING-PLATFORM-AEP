from langchain.agents.middleware import ContextEditingMiddleware, ClearToolUsesEdit

def context_editing_middleware():

    context_editing_middleware_ = ContextEditingMiddleware(edits = [ClearToolUsesEdit(trigger = 5000, clear_at_least = 0,
    keep = 5, clear_tool_inputs = True, exclude_tools=[], placeholder = "cleared")]) 

    return context_editing_middleware_