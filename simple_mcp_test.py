import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_mcp_connection():
    """Simple test to debug MCP connection"""
    
    # Get server command from user
    server_command = input("Enter your MCP server command (e.g., 'python server.py'): ")
    command_parts = server_command.split()
    
    try:
        print(f"Testing connection to: {command_parts}")
        
        server_params = StdioServerParameters(
            command=command_parts[0],
            args=command_parts[1:] if len(command_parts) > 1 else []
        )
        
        print("Creating stdio client...")
        
        # Try the basic pattern from MCP docs
        async with stdio_client(server_params) as (read, write):
            print("Got read/write streams")
            
            async with ClientSession(read, write) as session:
                print("Created session")
                
                # Initialize
                print("Initializing session...")
                result = await session.initialize()
                print(f"Initialize result: {result}")
                
                # List tools
                print("Listing tools...")
                tools = await session.list_tools()
                print(f"Tools: {tools}")
                
                if tools.tools:
                    for tool in tools.tools:
                        print(f"  - {tool.name}: {tool.description}")
                else:
                    print("  No tools found")
                
                print("Connection test successful!")
                
    except Exception as e:
        print(f"Connection failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(test_mcp_connection())