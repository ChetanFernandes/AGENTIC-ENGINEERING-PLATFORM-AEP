from app.router.schemas import Route , RouteDecision
route = Route(agent = "security", task = "look for security vulna", priority = 2)
route_decison = RouteDecision(routes = [route], execution_mode = "parallel", confidence = 0.4, routing_reason = "abcfdgarg")
print(route_decison)
