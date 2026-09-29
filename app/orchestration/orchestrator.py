
from app.schemas.custom_schemas import CustomState
from logger.log import setup_logging
log = setup_logging()


class RouteOrchestor:

    def __init__(self):
        self.agent_no_dependencies = {}
        self.agent_with_dependencies = {}
        self.agent_ready_to_execute = []
        self.route_executed = []
        self.route_failed = []
  

    async def execution_director(self, state:CustomState):
        try:
            route_decision = state["routing_information"]

            self.route_executed = state.get("successful_route_executed","NA")

            self.route_failed = state.get("failed_route_executed",'NA')

            log.info("Agent route executed successfully %s",  self.route_executed)
            log.info("Agent route failed or blokced %s",    self.route_failed)


            log.info("Routing_Decision:%s", route_decision.routes)

            for route in route_decision.routes:

                dependencies = route.dependencies

                if dependencies:

                    self.agent_with_dependencies[route.route_id] = {"route_id" : route.route_id  ,"agent" : route.agent , "dependencies" : route.route_id, "task":route.task }

                else:

                    self.agent_no_dependencies[route.route_id] = {"route_id" : route.route_id , "agent" : route.agent,"task":route.task}

        
            log.info("Agent_with_dependencies: %s",  self.agent_with_dependencies)
            log.info("Agent_with_no_dependencies: %s",  self.agent_no_dependencies)

            length_of_routes = len(route_decision.routes)

            log.info("Length of routes: %s", length_of_routes)

            self.agent_ready_to_execute = []

            # Find no-dependency agent that are not executed yet
            for route in self.agent_no_dependencies.values():
                if route["route_id"] not in self.route_executed and route["route_id"] not in self.route_failed: #in checks fo keys
                    self.agent_ready_to_execute.append(route)

            #Find dependency agents that are now ready
            for route in self.agent_with_dependencies.values():
                if route["route_id"] not in self.route_executed and route["route_id"] not in self.route_failed:
                    if self.check_dependency_agent(route["dependencies"]):
                        self.agent_ready_to_execute.append(route)

            #check for dead lock
            completed_routes = (set(self.route_executed.keys())) | set(self.route_failed.keys())
            
            if len(completed_routes) == length_of_routes:
                 log.info("All routes completed.")
                 return {"ready_routes": []}
            
            if not self.agent_ready_to_execute:
                raise RuntimeError("No agents are ready, but workflow is not complete")

            # Execute ALL ready agents
            log.info(f"Agent_ready_to_execute_-> {self.agent_ready_to_execute}")

            return {
                        
                    "ready_routes": [  
                                        { 
                                            
                                            "route_id":route["route_id"],
                                            "agent": route["agent"],  
                                            "task": route["task"]
                                        }
                                        for route in self.agent_ready_to_execute


                                    ]
                    }
        except Exception:
            log.exception("Orchestrator node failed")


    def check_dependency_agent(self,dependency_routes):
        return (all(dependency in self.route_executed for dependency in dependency_routes))



            #sorted_agents_dependency = sorted(self.agent_with_dependencies.values(),  key = lambda x : x["priority"])
            #sorted_agents_no_dependency = sorted(self.agent_no_dependencies.values(), key = lambda x : x["priority"
               
'''
result = await self.agent_executor.graph.ainvoke(self.state, config , context = context) # this return overall langraph state

while "__interrupt__" in result:

print("🔥 GRAPH INTERRUPT CAUGHT IN DEEP_AGENT_EXECUTOR")

print(result["__interrupt__"][0].value["action_requests"])
print(result["__interrupt__"][0].value["review_configs"])


decision = input("Do you want to approve or reject this tool call? ").strip().lower()
    
if decision in ["approve","reject"]:
result = await self.agent_executor.graph.ainvoke(  
                                    Command(resume={
                                            "decisions": [
                                                {"type": decision} #"reject"
                                            ]
                                        }
                                    ),
                                    config = config,
                                    context = context,
                                    )  



print("\n========== CHECKPOINT TEST ==========")


    

    else:


        log.info("sucessfully executed agent:%s -> wave:%s", agent , wave)

        self.route_executed.append(route_id)
        
        log.info("Agent executed list:%s",self.route_executed)


except Exception:
log.exception("Orchestration_agent execution failed")
self.route_failed.append(route_id)
''' 
      




         



#Python orchestrator state → LangGraph execution state → node → updated LangGraph state → Python orchestrator state.
        
#self.state["context_given_agent"] = state_result["context_given_agent"]

#self.agents_outputs  = state_result["agents_outputs"]

#log.info("Context used by agent: %s, context:\n%s", agent, pformat(self.state["context_given_agent"].get(agent,"Na")))

#log.info("Output produced by agent: %s, output:\n%s", agent, pformat(self.agents_outputs[agent]))
                
                
   
'''
            task
            Observation:
            /workspace/weatherapp did not exist.

            Action:
            Created workspace and cloned repository.

            Lesson:
            Sandbox starts without repository directories.
            Before repository operations, create the workspace and clone
            the repository into /workspace/<repo-name>.

            async def main():

                route_orchester = RouteOrchestor()
                
                question =  
                                create readme file for repo https://github.com/ChetanFernandes/Map-Reduce-Filter-Recursion-Function
                
                            

                await route_orchester.execution_director(question)



            if __name__ == "__main__":
                loop = asyncio.SelectorEventLoop()
                asyncio.set_event_loop(loop)

                try:
                    loop.run_until_complete(main())
                finally:
                    loop.close()


'''