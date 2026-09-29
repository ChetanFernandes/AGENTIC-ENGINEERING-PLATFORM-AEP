from llm_config import llm_openai
from langchain_core.prompts import ChatPromptTemplate
from logger.log import setup_logging
log = setup_logging()
from pydantic import BaseModel

class LLMOutput(BaseModel):
    selected_data: str


system_prompt = '''
            1. Youre expert in extracting the content required to solve the task effectively from the given data. 
            2. The content will be passed to agent to solve the task.
            3. Your task is to check data and extract only required content to solve the task
            4. Dont create your own content. Use content from the given data, if needed.
            5. Information related to task, data are given below
                task - {task}
                available_data - {data}
            '''



def content_extraction(task:str,data:str):

    structured_llm = llm_openai.with_structured_output(LLMOutput)

    template = ChatPromptTemplate.from_messages([  ('system' , system_prompt),
                                                   ("humnan", "Task : {task}\n, available_data : {data}" ) 
                                                ])

    relevance_chain = template | structured_llm

    result = relevance_chain.invoke({"task": task,"data": data})
    
    return result
    




