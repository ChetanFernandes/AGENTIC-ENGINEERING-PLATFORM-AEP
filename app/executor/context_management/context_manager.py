from app.executor.context_management.agent_context_schema import Context
from app.schemas.custom_schemas import CustomState
from app.executor.context_management.context_policy import ContextPolicy
from app.executor.context_management.optional_context_relevance import ContextRelevanceSelector
#from app.executor.context_management.allowed_context_relevance import content_extraction
#from app.executor.langgraph.reducer import merge
from pprint import pformat
from logger.log import setup_logging
log = setup_logging()

class ContextManager():

    def __init__(self):
        self.context_policy = ContextPolicy()
        self.context_relevance = ContextRelevanceSelector()

    async def build_context(self, agent, task , user_id, store_backend, state) -> Context:
        try:

            log.info("Building context for agent: %s", agent)

            # allowed sources

            allowed_agent_sources = self.context_policy.get_allowed_sources(agent)
            optional_agent_sources = self.context_policy.get_optional_sources(agent) 

            log.info("Allowed sources to extract content for agent:%s -> sources:%s", agent, allowed_agent_sources)
            log.info("Optional sources to extract content for agent:%s -> sources:%s", agent, optional_agent_sources)

            # Extracting output for selected source agent
              
            log.info("Extracting context for agent:%s", agent)

            allowed_context = {}

            for source_agent in allowed_agent_sources:

                artifacts_id = state["artifacts_id"].get(source_agent)
                print("%s for %s", artifacts_id, source_agent)

                if artifacts_id:
                    try:
                        allowed_context_data = await store_backend.get_agent_output(user_id, artifacts_id)
                        allowed_context[source_agent] = allowed_context_data
                        
                    except Exception:
                        log.exception("Error while extracting context from allowed sources")

                else:
                    log.info("%s not yet executed",source_agent)

            optional_context = {}

            for source_agent in optional_agent_sources:

                artifacts_id = state["artifacts_id"].get(source_agent)

                if artifacts_id:
                    try:
                        optional_context_data = await store_backend.get_agent_output(user_id, artifacts_id)
                        optional_context[source_agent] = optional_context_data

                    except Exception:
                        log.exception("Error while extracting context from optional sources")

                else:
                    log.info("%s not yet executed",source_agent)


            if allowed_context or optional_context:

                final_context_data = await self.context_relevance.select_relevant_context(task, allowed_context, optional_context)

                log.info("Extracting context completed for %s, content:%s", agent, pformat(final_context_data))

                return Context(context = final_context_data)

            else:
                return Context(context = {})
            
        except Exception:
            log.exception("Build context failed")
        






