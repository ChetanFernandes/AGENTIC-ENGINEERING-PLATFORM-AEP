from fastmcp import FastMCP

mcp = FastMCP("Simple MCP Server")

@mcp.tool()
def add(a:int,b:int)-> int:
    """Add two numbers."""
    return a + b

if __name__ == "__main__":
    mcp.run(transport="stdio") # It tells FastMCP: Start this MCP server and communicate with the MCP client through stdin/stdout."