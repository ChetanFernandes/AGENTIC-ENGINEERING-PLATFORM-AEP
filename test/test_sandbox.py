from dotenv import load_dotenv
load_dotenv()
print("STARTING SANDBOX TEST")

'''
from langsmith.sandbox import SandboxClient

print("CREATING CLIENT")
client = SandboxClient()

print("CREATING SANDBOX")
with client.sandbox() as sb:
    print("SANDBOX CREATED")
    result = sb.run("python3 -c 'import sys; print(sys.version)'")
    print("RESULT:", result)




from deepagents.backends.langsmith import LangSmithSandbox
from langsmith.sandbox import SandboxClient

client = SandboxClient()
ls_sandbox = client.create_sandbox()
backend = LangSmithSandbox(sandbox=ls_sandbox)

result = backend.execute("python --version")
print(result.output)
'''

import inspect
from deepagents.backends import LangSmithSandbox

print(inspect.getsource(LangSmithSandbox))