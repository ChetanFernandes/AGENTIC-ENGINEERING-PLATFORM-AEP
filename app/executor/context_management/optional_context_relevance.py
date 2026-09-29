from langchain_core.prompts import ChatPromptTemplate
from config.llm_config import llm_openai
from pydantic import BaseModel , Field
from logger.log import setup_logging
log = setup_logging()
from typing import Any

class SelectedSourceContext(BaseModel):
    status: str
    summary: str
    errors: list[str]
    relevant_details: str | None = None

class LLMOutput(BaseModel):
     selected_context: dict[str, SelectedSourceContext] = Field(default_factory=dict)

class ContextRelevanceSelector:
    pass

    async def  select_relevant_context(self, task, source_1 = {}, source_2 = {} ):
        
        system_prompt = '''
            1. You are an expert in extracting the content required to solve the task effectively from the given sources.
            2. The content extracted by you will be passed to the agent to solve the task.
            3. The source data is provided as Python dictionaries containing key-value pairs.
            4. The key represents the source/topic name, such as repository, security, architecture, etc.
            5. The value contains the content produced by that source/topic.
            6. Use the key to identify the source and extract only the relevant portions from its value.
            7. Do not create your own content. Extract content only from the sources.
            8. If source_1 is empty, extract content only from source_2 and vice versa.
            9. If a source has no relevant information, do not include that source in selected_context.
            10. Return the extracted content grouped by source name.
            11. Always preserve the source's status, summary, and errors in selected_context.
                From result and metadata, extract only the information relevant to the task.
            12. For each selected source, return the information using these fields:
                - status: copy the source's status exactly.
                - summary: copy the source's summary exactly.
                - errors: copy the source's errors exactly.
                - relevant_details: extract only the portions of result or metadata that are relevant to the task.
            13. Do not modify, summarize, or invent the status, summary, or errors.
            14. Preserve failure information and pass it to the next agent; do not exclude a source merely because its status indicates failure
            15. Information related to the task and sources:
                task - {task}
                source_1 - {source_1}
                source_2 - {source_2}
        '''
        
        structured_llm = llm_openai.with_structured_output(LLMOutput, method="function_calling")

        template = ChatPromptTemplate.from_messages([ ("system", system_prompt) , 
                                                      ("human" , "Task: {task}\n source_1: {source_1},  source_2: {source_2}")
                                                    ])

        relevance_chain = template | structured_llm

        result = await relevance_chain.ainvoke({"task" : task , "source_1" : source_1 ,"source_2" : source_2})

        log.info("Output producted by LLM:%s" , result.selected_context)
        
        return result.selected_context



''' 
  
1. Youre expert in finding the content(context) from the optional sources required to solve the given task, apart from already present in available_ouputs
2. The context will be passed to agent to resove the task.
3. The optional sources and available_sources is a python dictionary type having Key and Value 
4. The"key" being topics. For example - security, archieture, etc.. 
5. The value being topic content dervied from repositories.
6. Your task is to check available_sources and refer if anything extra content is required from optional sources to resolve the task.
7. As per your analysis if extra context is needed from optional sources than,
    Return only the names of selected optional sources that are present in optional_sources. Do not return any source that is not present there.
8. If content already present in available_sources is sufficient to resolve the task, then dont add any content from optional_sources.
9. Adding content from optional sources is not mandatory.
10. Dont create your own content. Use content from the optional sources only, if needed.
11. Information related to task, optional_source and available_sources are given below
    task - {task}
    optional_sources - {optional_sources}
    available_sources - {allowed_sources}

''' 
        



        
