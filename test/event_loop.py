import time,asyncio

async def addition():
    await asyncio.sleep(5)
    print(5+6)

async def sum():
    await addition()

async def multiplication():
    print(5*5)

async def main():
    await asyncio.gather(sum(),multiplication())

asyncio.run(main())

from fastmcp.client.group import ClientGroup
from fastmcp import Client


def create_github_client():

    return Client("https://api.githubcopilot.com/mcp/")

client_group = ClientGroup({"github_1":create_github_client(),"github_2":create_github_client()})
print(client_group)
print(type(client_group))
print([x for x in dir(client_group) if not x.startswith("_")])
print(client_group.clients)



