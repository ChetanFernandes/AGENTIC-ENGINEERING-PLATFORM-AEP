from deepagents import create_deep_agent
from deepagents.backends import LangSmithSandbox
from langsmith.sandbox import SandboxClient
from llm_config import llm_openai , llm_ollama
from pprint import pprint

client = SandboxClient()
ls_sandbox = client.create_sandbox()
backend = LangSmithSandbox(sandbox=ls_sandbox)
#backend.execute("echo 'Hello from the LangSmith sandbox' > /tmp/test.txt")

print("SANDBOX:", ls_sandbox.name)

reducer_code = b"""

def merge(current_output:dict , update_sate_output:dict) -> dict:
    return {**current_output , ** update_sate_output}

if __name__ == "__main__":
    current = {"agent1": "output1"}
    update = {"agent2" : "output2"}
    result = merge(current,update)
    print(result)

"""

backend.upload_files(
    [
        ("/src/reducer.py", reducer_code),

    ]
)

agent = create_deep_agent(
    model=llm_openai,
    system_prompt= "You are a Python coding assistant with sandbox access. Use the sandbox to execute commands when required.",         
    backend=backend,
)

result = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": 
                              'Run the Python file /src/reducer.py in the sandbox and store the output in path "/temp/output.txt"'
                           

            }
        ]
    }
)


results = backend.download_files(["/temp/output.txt"])

for result in results:
    if result.content is not None:
        print(f"{result.path} : {result.content.decode()}")
    else:
        print(f"Failed to download {result.path}: {result.error}")


#pprint(results)
#pprint(results['messages'][-1].content)



     