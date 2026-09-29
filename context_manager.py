'''
class MyResource():

    def __init__(self):
        pass

    def __enter__(self):
        print("Opening") 
        return "My connection"


    def multiply(self):
        return 7*6

    def __exit__(self,exc_type, exc_value, traceback):
        print("Exit function")

with MyResource() as resource:
    print(resource)

# -------------------------------------------

class MyResource():

    def __init__(self):
        pass

    def __enter__(self):
        print("Opening") 
        return self


    def multiply(self):
        return 7*6

    def __exit__(self,exc_type, exc_value, traceback):
        print("Exit function")

with MyResource() as resource:
    print(resource.multiply())


#-----------------------------------------
'''
import asyncio

class MyResource_1():

    def __init__(self):
        pass

    async def __aenter__(self):
        print("Opening") 
        return self


    def multiply(self):
        return 7*6

    async def __aexit__(self,exc_type, exc_value, traceback):
        print("Exit function")

async def main():
    async with MyResource_1() as conn:
        print(conn)
        print(conn.multiply())

asyncio.run(main())

'''
What is actually happening?

This:

with MyResource() as resource:
    print(resource)

is roughly equivalent to:

resource_manager = MyResource()

resource = resource_manager.__enter__()

try:
    print(resource)
finally:
    resource_manager.__exit__(None, None, None)
'''
'''
AsyncExitStack
│
├── __aenter__()   ← called when entering `async with`
│
├── enter_async_context()  ← used to add/manage another resource
│
└── __aexit__()    ← called when leaving `async with`

AsyncExitStack
    │
    └── __aenter__()     ← starts the STACK

Connection
    │
    └── __aenter__()     ← starts the CONNECTION

The first one starts the manager.
The second one starts the resource being managed.

That's the distinction I want you to get clearly before we go further.

async with AsyncExitStack() as stack:

    conn1 = await stack.enter_async_context(MCP1)

    conn2 = await stack.enter_async_context(MCP2)

    conn3 = await stack.enter_async_context(MCP3)

    # use all connections

You can keep adding resources inside a loop:

async with AsyncExitStack() as stack:

    for server in servers:
        connection = await stack.enter_async_context(server)
'''