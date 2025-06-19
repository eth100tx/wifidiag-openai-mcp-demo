# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python desktop application that bridges MCP (Model Context Protocol) servers with ChatGPT, enabling ChatGPT to execute custom tools through a GUI interface. The app uses Tkinter for the GUI, OpenAI's API for ChatGPT integration, and the MCP protocol for tool execution.

## Common Development Commands

### Setup and Installation
```bash
pip install -r requirements.txt
cp .env.template .env  # Then edit with your OpenAI API key
```

### Running the Application
```bash
python mcp_chatgpt_client.py         # Main GUI application
python simple_mcp_test.py            # Test MCP server connections
python wifi_diagnostics_mcp.py       # Example MCP server (standalone)
```

### Testing MCP Integration
```bash
python simple_mcp_test.py            # Interactive MCP connection testing
```

### Windows Automation
```bash
start.bat                           # Automated setup and launch (Windows)
```

## Architecture

### Core Components
- **mcp_chatgpt_client.py**: Main GUI application with threading architecture
- **wifi_diagnostics_mcp.py**: Example MCP server providing system diagnostic tools  
- **simple_mcp_test.py**: Standalone MCP connection testing utility

### Threading Architecture
The application uses a 3-thread model:
- **GUI Thread**: Tkinter interface and user interactions
- **Async Worker Thread**: OpenAI API calls and MCP tool execution  
- **Setup Threads**: Background initialization of OpenAI/MCP connections

**Inter-thread Communication**: Uses thread-safe queues (`message_queue`, `response_queue`, `status_queue`) with polling-based GUI updates every 100ms.

### MCP Integration Pattern
- **Stateless Connections**: New MCP connection created per tool execution
- **Tool Discovery**: MCP tools discovered once and cached, then converted to OpenAI function format
- **Schema Translation**: Automatic conversion between MCP tool schemas and OpenAI function calling format

### Configuration Management
- **Environment Variables**: Load from `.env` file via python-dotenv
- **Runtime Dialogs**: Interactive prompts for missing OpenAI API key or MCP server command
- **Defaults**: MCP server defaults to `python wifi_diagnostics_mcp.py`

## Key Files and Their Purposes

| File | Purpose |
|------|---------|
| `mcp_chatgpt_client.py` | Main GUI application - handles ChatGPT integration, MCP communication, and threading |
| `wifi_diagnostics_mcp.py` | Example MCP server providing 6 WiFi diagnostic tools via PowerShell commands |
| `simple_mcp_test.py` | Debugging utility for testing MCP server connections independently |
| `requirements.txt` | Python dependencies: openai, mcp, python-dotenv |
| `.env` | Configuration file (created from .env.template) |
| `start.bat` | Windows batch script for automated environment setup and application launch |

## Development Patterns

### Error Handling
- All major operations wrapped in try-catch blocks
- Errors propagated through queue system to GUI with user-friendly messages
- Full stack traces logged to console for debugging
- Graceful degradation (ChatGPT works without MCP tools if connection fails)

### MCP Server Development
- Use `fastmcp` library for rapid MCP server creation
- Implement proper input validation and error messages
- Set reasonable timeouts (default 30s) for system operations
- Handle Windows admin privileges gracefully in diagnostic tools

### GUI Updates
- Never update GUI components directly from worker threads
- Always use queue system for thread-safe GUI updates
- Status updates via `status_queue` for real-time user feedback
- Color-coded message display (user: blue, assistant: green, system: red)

### Tool Execution Flow
1. User sends message → `message_queue`
2. Worker thread processes via OpenAI API with tool definitions
3. If ChatGPT calls tools → create new MCP connection per tool
4. Tool results fed back to ChatGPT for final response
5. Final response → `response_queue` → GUI display

## Configuration Options

### Environment Variables (.env file)
- `OPENAI_API_KEY`: Required OpenAI API key
- `MCP_SERVER_COMMAND`: Optional default MCP server command
- `DEBUG_LEVEL`: Optional logging verbosity (INFO, DEBUG, etc.)
- `OPENAI_MODEL`: Optional ChatGPT model (defaults to gpt-4)
- `WINDOW_SIZE`: Optional GUI window dimensions
- `THEME`: Optional UI theme

### Runtime Configuration
- OpenAI API key prompt if missing from environment
- MCP server command dialog with sensible default
- All settings stored in class instance (not persisted)

## Dependencies

**Core Dependencies (requirements.txt):**
- `openai>=1.0.0`: OpenAI API client for ChatGPT integration
- `mcp>=1.0.0`: Model Context Protocol client/server libraries
- `python-dotenv>=0.19.0`: Environment variable loading

**Standard Library Usage:**
- `tkinter`: GUI framework
- `asyncio`: Async operations for MCP and OpenAI
- `threading` + `queue`: Thread-safe communication
- `subprocess`: System command execution (in MCP servers)

## Common Debugging Scenarios

### "MCP connection failed"
1. Test MCP server independently: `python simple_mcp_test.py`
2. Verify MCP server command is correct
3. Check if MCP server starts without errors when run directly

### "No tools found" 
1. Verify MCP server implements `list_tools()` correctly
2. Check MCP server starts up and responds to protocol messages
3. Ensure tool definitions have proper schemas

### "OpenAI API failed"
1. Verify API key in `.env` file
2. Check API key permissions and usage limits
3. Test API connection separately from MCP integration

### Tool execution timeout
1. Check if admin privileges required for diagnostic tools
2. Increase timeout values in MCP server implementation
3. Verify PowerShell commands work when run manually (Windows)