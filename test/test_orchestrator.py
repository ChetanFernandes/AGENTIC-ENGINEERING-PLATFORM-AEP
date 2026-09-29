from app.router.schemas import Route, RouteDecision
from app.orchestration.orchestrator import RouteOrchestor
import pytest
mock_result = RouteDecision(routes = [ 
                                        Route(
                                                    agent = "security",
                                                    task = "Review the application for security vulnerabilities",
                                                    priority = 1,
                                                    dependencies=[]
                                             ),

                                    ],

                            execution_mode="sequential",
                            confidence=0.9,
                            routing_reason="Security review is required."

                            )

def test_execution_director():
        route = RouteOrchestor()
        route.execution_director(mock_result)







