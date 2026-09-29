from config.llm_config import llm_openai
from app.router.schemas import RouteDecision
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from app.router.prompts import ROUTER_SYSTEM_PROMPT
from uuid_utils import uuid7
from app.schemas.custom_schemas import RuntimeContextSchema
from logger.log import setup_logging
log = setup_logging()


chat_template = ChatPromptTemplate.from_messages([
                                                    ("system", ROUTER_SYSTEM_PROMPT), 
                                                    ("human", "{user_request}")
                                                ])

structured_llm = llm_openai.with_structured_output(RouteDecision)

router_chain = chat_template | structured_llm

class RequestContext:

    def __init__(self):

        self.user_id = "Chetan_1"
        
        self.config = {"configurable" : {"thread_id" : str(uuid7())[:8]},
                       
                       "metadata":{"user_id": self.user_id}}
        
        self.context = RuntimeContextSchema(user_id = self.user_id )

    def route_request(self, question: str) -> RouteDecision:
        """Analyze a user request and return a routing decision."""
        try:
            log.info("Route request received")

            if not question.strip():
                raise ValueError("Question cannot be empty or whitespace")

            result = router_chain.invoke({"user_request" : question})

            return result , self.config , self.context

        except ValueError as e:
            log.error(str(e))
            raise

        except Exception as e:
            log.exception("Route_request_failed: %s",str(e))
            raise






