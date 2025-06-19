# Technical Documentation: MCP-ChatGPT Bridge

## Architecture Overview

### System Components
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │
│   GUI Client    │    │   MCP Server    │    │  OpenAI API     │
│   (tkinter)     │◄──►│  (Python/Node)  │    │   (ChatGPT)     │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                        │                        │
        │                        │                        │
    Threading              MCP Protocol              Function Calls
    + Queues              (stdio transport)          (JSON-RPC-like)
```

### Data Flow
1. **User Input** → GUI Thread → Message Queue
2. **Message Queue** → Async Worker Thread
3. **Async Worker** → OpenAI API (with tool definitions)
4. **ChatGPT Response** → Tool Call Detection
5. **Tool Execution** → MCP Server (new connection per call)
6. **Tool Results** → Back to ChatGPT for final response
7. **Final Response** → Response Queue → GUI Display

### Threading Model
- **Main Thread**: Tkinter GUI and user interaction
- **Setup Thread**: Initial OpenAI/MCP connection setup
- **Worker Thread**: Async ChatGPT communication and tool execution
- **Communication**: Thread-safe queues for message passing

## MCP Integration Details

### Server Connection Management
```python
# New connection per tool call (stateless)
async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        result = await session.call_tool(tool_name, arguments)
```

**Why New Connections?**
- Ensures clean state for each tool execution
- Prevents connection corruption from long-running operations
- Handles MCP server crashes gracefully
- Simplifies error recovery

### Tool Schema Translation
MCP tools are automatically converted to OpenAI function format:
```python
# MCP Tool
{
    "name": "check_wifi_status",
    "description": "Check current WiFi adapter status",
    "inputSchema": {"type": "object", "properties": {}}
}

# OpenAI Function
{
    "type": "function",
    "function": {
        "name": "check_wifi_status",
        "description": "Check current WiFi adapter status",
        "parameters": {"type": "object", "properties": {}}
    }
}
```

### Error Handling Strategy
- **Connection Errors**: Retry with exponential backoff
- **Tool Execution Errors**: Return error message to ChatGPT
- **API Errors**: Display to user with retry option
- **Timeout Handling**: 30-second timeout per tool execution

## Configuration & Customization

### Environment Variables
```bash
OPENAI_API_KEY=sk-...          # Required: Your OpenAI API key
MCP_SERVER_COMMAND=python ...  # Optional: Default MCP server command
DEBUG_LEVEL=INFO               # Optional: Logging verbosity
```

### Client Modifications

#### Change ChatGPT Model
```python
# In chat_with_gpt method (lines 145, 174)
response = self.openai_client.chat.completions.create(
    model="gpt-3.5-turbo",  # Change from "gpt-4"
    messages=self.chat_history,
    tools=tools,
    tool_choice="auto" if tools else None
)
```

#### Adjust Window Appearance
```python
# In setup_gui method
self.root.geometry("1200x800")  # Wider window
self.root.configure(bg="dark gray")  # Dark theme
```

#### Modify Tool Timeout
```python
# In MCP server (wifi_diagnostics_mcp.py)
result = subprocess.run(
    cmd,
    capture_output=True,
    text=True,
    shell=shell,
    timeout=60  # Increase from 30 seconds
)
```

#### Add Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Add throughout code:
logging.info(f"Executing tool: {tool_name}")
logging.error(f"Tool execution failed: {e}")
```

### MCP Server Development

#### Required Components
```python
# Using fastmcp (recommended)
from fastmcp import FastMCP
mcp = FastMCP("Your Server Name")

@mcp.tool()
def your_function(param: str) -> str:
    """Tool description for ChatGPT"""
    return "result"

if __name__ == "__main__":
    mcp.run()
```

#### Using Standard MCP
```python
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("Your Server")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [Tool(name="your_tool", description="Description")]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "your_tool":
        return [TextContent(type="text", text="Result")]
```

#### Best Practices
- **Input Validation**: Always validate tool parameters
- **Error Messages**: Return helpful error descriptions
- **Timeouts**: Implement reasonable timeouts for long operations
- **Permissions**: Handle admin/permission requirements gracefully
- **Documentation**: Clear descriptions for ChatGPT to understand usage

## Performance Optimization

### Connection Pooling (Future Enhancement)
```python
# Potential improvement: connection reuse
class MCPConnectionPool:
    def __init__(self, server_params, pool_size=3):
        self.server_params = server_params
        self.pool = asyncio.Queue(maxsize=pool_size)
        
    async def get_connection(self):
        # Reuse existing connection if available
        # Create new if pool empty
        pass
```

### Caching Tool Definitions
```python
# Cache tool schema to avoid repeated MCP calls
self.tool_cache = {}
if not self.tool_cache:
    tools_result = await session.list_tools()
    self.tool_cache = {tool.name: tool for tool in tools_result.tools}
```

### Async Improvements
```python
# Parallel tool execution for multiple tools
async def execute_multiple_tools(self, tool_calls):
    tasks = []
    for call in tool_calls:
        task = asyncio.create_task(
            self.execute_mcp_tool(call.function.name, call.arguments)
        )
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    return results
```

## Security Considerations

### API Key Protection
- Store in environment variables or `.env` file
- Never commit keys to version control
- Use key rotation policies
- Monitor API usage for anomalies

### MCP Server Security
```python
# Input sanitization
def validate_input(data):
    if not isinstance(data, dict):
        raise ValueError("Invalid input format")
    
    # Sanitize file paths
    if 'path' in data:
        path = os.path.normpath(data['path'])
        if '..' in path:
            raise ValueError("Path traversal not allowed")
```

### Network Security
- Use HTTPS for all external API calls
- Validate certificates for external connections
- Implement rate limiting for tool executions
- Log security-relevant events

### Permission Management
```python
# Check admin requirements
def requires_admin():
    import ctypes
    return ctypes.windll.shell32.IsUserAnAdmin()

def safe_system_operation(command):
    if not requires_admin():
        return "This operation requires administrator privileges"
    # Proceed with operation
```

## Debugging & Diagnostics

### Enable Debug Output
```python
# Add to main()
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

### MCP Connection Testing
Use `simple_mcp_test.py` to isolate MCP issues:
```python
# Test specific tools
async def test_specific_tool():
    # ... connection setup ...
    result = await session.call_tool("check_wifi_status", {})
    print(f"Tool result: {result}")
```

### OpenAI API Testing
```python
# Test API without MCP
client = openai.OpenAI(api_key=api_key)
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)
print(response.choices[0].message.content)
```

### Common Debug Scenarios

#### "MCP connection failed"
```bash
# Test server manually
python wifi_diagnostics_mcp.py
# Should start without errors

# Check server output
python simple_mcp_test.py
# Follow prompts to test connection
```

#### "Tool execution timeout"
```python
# Increase timeout in server
subprocess.run(..., timeout=60)

# Or check for blocking operations
import signal
def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(30)  # 30 second timeout
```

#### "ChatGPT not using tools"
```python
# Verify tool descriptions are clear
tools = self.mcp_tools_to_openai_format()
print(json.dumps(tools, indent=2))

# Check if tools are being sent
print(f"Tools available: {len(tools) if tools else 0}")
```

## Deployment Considerations

### Packaging for Distribution
```bash
# Create standalone executable
pip install pyinstaller
pyinstaller --onefile --windowed mcp_chatgpt_client.py
```

### Configuration Management
```python
# Config file support
import configparser

config = configparser.ConfigParser()
config.read('settings.ini')

DEFAULT_MODEL = config.get('openai', 'model', fallback='gpt-4')
WINDOW_SIZE = config.get('ui', 'window_size', fallback='800x600')
```

### Error Reporting
```python
# Crash reporting
import traceback
import datetime

def log_crash(error):
    with open('crash_log.txt', 'a') as f:
        f.write(f"{datetime.datetime.now()}: {str(error)}\n")
        f.write(traceback.format_exc())
        f.write("\n" + "="*50 + "\n")
```

## Future Enhancements

### Multiple MCP Servers
- Support connecting to multiple MCP servers simultaneously
- Tool namespace management to prevent conflicts
- Load balancing across server instances

### Plugin Architecture
- Dynamic loading of MCP servers
- Plugin marketplace/registry
- Automatic updates for tools

### Advanced UI Features
- Syntax highlighting for code responses
- File upload/download capabilities
- Voice input/output integration
- Mobile companion app

### Enterprise Features
- User authentication and authorization
- Audit logging and compliance
- Team collaboration features
- Integration with enterprise tools (Slack, Teams, etc.)

---

**Contributing:**
- Fork the repository and submit pull requests
- Follow Python PEP 8 style guidelines  
- Add tests for new functionality
- Update documentation for changes