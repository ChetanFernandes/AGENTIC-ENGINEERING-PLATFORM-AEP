from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel , Field, field_validator
from logger.log import setup_logging
log = setup_logging()

class SelectedSourceContext(BaseModel):
    status: str | None = None
    summary: str | None = None
    errors: list[str] = Field(default_factory=list)
    relevant_details: str | None = None

    @field_validator("errors",mode = 'before')
    @classmethod
    def normalize_errors(cls,value):
        if value is None:
            return []
        return value

class LLMOutput(BaseModel):
     selected_context: dict[str, SelectedSourceContext] = Field(default_factory=dict)

class ContextRelevanceSelector:
    pass

    async def  select_relevant_context(self, task, llm_openai, source_1 = {}, source_2 = {}):
        system_prompt = '''
        You are a context selection component in a multi-agent engineering platform.

        Your responsibility is to extract task-relevant information from the provided sources and pass it to the downstream agent.

        ## Rules

        1. Treat `source_1` and `source_2` as the only authoritative sources. Do not use external knowledge or invent content.

        2. Select only information explicitly present in the source data and directly relevant to the given task.

        3. For every selected source, preserve these fields exactly as provided:
        - status
        - summary
        - errors

        4. Populate `relevant_details` using only information explicitly present in the source's `result` or `metadata`.

        5. Do not create new findings, recommendations, explanations, summaries, or instructions. Do not rewrite extracted evidence into new statements.

        6. Exclude unrelated content, including conversation-recovery instructions, execution-resumption notes, internal workflow instructions, and unrelated historical context, unless explicitly required by the task.

        7. Do not treat a file's existence as proof of a vulnerability. Preserve the source's stated limitations, uncertainty, and missing evidence.

        8. Do not combine unrelated information from different sources into a new narrative. Group selected content under its original source name.

        9. If a source has no relevant information, omit it from `selected_context`. If only part of a source is relevant, select only that part.

        10. If a source reports that an investigation or scan was not completed, preserve that limitation. Never imply that the investigation was completed.

        11. Do not create missing information to satisfy the downstream task. The downstream agent must be able to recognize when evidence is insufficient.

        12. When relevance is uncertain, exclude the questionable content rather than introducing potentially unrelated information.

        13. Return only the requested structured output. Do not add commentary outside the output schema.

        For the output schema:
        - The errors field must always be a list of strings.
        - If the source errors field is null or missing, return an empty list [].
        - Never return null for errors.
        - Preserve all actual error messages without changing their content.

        ## Task and sources

        Task: {task}

        Source 1: {source_1}

        Source 2: {source_2}
        
        '''
     
        structured_llm = llm_openai.with_structured_output(LLMOutput, method="function_calling")

        template = ChatPromptTemplate.from_messages([ ("system", system_prompt) , 
                                                      ("human" , "Task: {task}\n source_1: {source_1},  source_2: {source_2}")
                                                    ])

        relevance_chain = template | structured_llm

        result = await relevance_chain.ainvoke({"task" : task , "source_1" : source_1 ,"source_2" : source_2})

        log.info("Content producted by LLM:%s" , result.selected_context)
        
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
        



        
