import pytest
from app.router.llm import route_request
from app.router.schemas import Route, RouteDecision
from unittest.mock import patch

def test_whitespace_question():
    with pytest.raises(ValueError): # I except following code to raise value error
        route_request("  ")


def test_empty_question():
    with pytest.raises(ValueError):
        route_request("")


def test_successful_routing():
    mock_result = RouteDecision(
        routes = [ 
             Route(
                   agent = "security",
                   task = "Review the application for security vulnerabilities",
                   priority = 1,
                   dependencies=[]
                    )
                ],
        execution_mode="sequential",
        confidence=0.9,
        routing_reason="Security review is required."
    )
    with patch("app.router.llm.router_chain") as mock_router_chain:
        mock_router_chain.invoke.return_value = mock_result
        result = route_request("Review the application for security vulnerabilities")

    assert isinstance(result,RouteDecision)
    assert result.routes[0].agent == "security"


              
                  
