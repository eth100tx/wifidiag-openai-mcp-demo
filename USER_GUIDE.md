# User Guide: MCP-ChatGPT Bridge Client

## Table of Contents
1. [Installation & Setup](#installation--setup)
2. [First Run](#first-run)
3. [Using the Application](#using-the-application)
4. [WiFi Diagnostics Demo](#wifi-diagnostics-demo)
5. [Troubleshooting](#troubleshooting)
6. [Advanced Usage](#advanced-usage)

## Installation & Setup

### System Requirements
- **Operating System:** Windows 10 or Windows 11
- **Python:** Version 3.8 or higher
- **Internet:** Active connection for OpenAI API
- **Permissions:** Administrator rights may be needed for some MCP tools

### Step 1: Install Python Dependencies
Open PowerShell in the project directory and run:
```powershell
pip install -r requirements.txt
```

**If you encounter the tkinter error:**
```
ERROR: Could not find a version that satisfies the requirement tkinter
```
This is normal - tkinter comes with Python on Windows. Just ignore this error.

### Step 2: Configure OpenAI API Key

**Option A: Using .env file (Recommended)**
1. Copy the `.env` file template content
2. Replace `your_openai_api_key_here` with your actual API key
3. Save the file

**Option B: Using PowerShell Environment Variable**
```powershell
$env:OPENAI_API_KEY = "your_actual_api_key_here"
```

### Step 3: Verify MCP Server
Make sure your MCP server file is working:
```powershell
python wifi_diagnostics_mcp.py
```
It should start without errors. Press `Ctrl+C` to stop it.

## First Run

### Starting the Application
```powershell
python mcp_chatgpt_client.py
```

### Setup Dialogs
The application will guide you through setup:

1. **API Key Prompt** (if not in .env)
   - Enter your OpenAI API key
   - The key is masked with asterisks for security

2. **MCP Server Command**
   - Default: `python wifi_diagnostics_mcp.py`
   - Press Enter to accept, or enter your custom command
   - Examples: `node my_server.js`, `python custom_tools.py`

### Status Indicators
Watch the bottom-left status bar:
- 🔵 "Starting up..." - Application initializing
- 🔵 "Connecting to OpenAI API..." - Testing API connection
- 🟢 "OpenAI API connected successfully" - API ready
- 🔵 "Connecting to MCP server..." - Starting your tools
- 🟢 "MCP connected. Available tools: ..." - Shows your tools
- 🎉 "Ready! You can now chat with ChatGPT using MCP tools" - All systems go!

## Using the Application

### Main Interface
The application window has three main areas:
- **Chat Display** - Conversation history with color coding
- **Input Field** - Type your messages here
- **Status Bar** - Connection and operation status

### Color Coding
- 🔵 **Blue** - Your messages
- 🟢 **Green** - ChatGPT responses
- 🟠 **Orange** - Tool execution notifications
- 🔴 **Red** - Error messages

### Sending Messages
- Type in the input field at the bottom
- Press **Enter** or click **Send**
- ChatGPT will respond and can use your MCP tools automatically

### Tool Execution
When ChatGPT uses your tools, you'll see:
```
🔧 Calling tool: check_wifi_status with {}
```
Then ChatGPT will analyze the results and respond with insights.

## WiFi Diagnostics Demo

### Quick Test
Ask ChatGPT:
```
Can you check my WiFi status?
```

### Comprehensive Diagnostic
For a complete analysis, copy and paste the content from `wifi_diagnostic_prompt.md`. This will guide ChatGPT through:
1. WiFi adapter status check
2. Network connectivity analysis  
3. Authentication review
4. Environment analysis
5. Comprehensive report generation

### Sample Conversation Flow
```
You: Can you check my WiFi status and diagnose any issues?

🔧 Calling tool: check_wifi_status with {}
🔧 Calling tool: diagnose_connection_issues with {}

ChatGPT: I've analyzed your WiFi setup. Here's what I found:

✅ WiFi Adapter Status: Your adapter is connected and functioning
⚠️  Signal Strength: 65% - Could be stronger
✅ Internet Connectivity: All tests passed
❌ DNS Issues: Experiencing some delays

Recommendations:
1. Move closer to your router
2. Consider switching to 5GHz band
3. Flush DNS cache for better performance
```

### Automatic Fixes
If issues are found, ChatGPT may suggest:
```
Would you like me to attempt automatic fixes? I can:
- Reset your WiFi adapter
- Flush DNS cache
- Renew IP address
- Reset network stack
```

## Troubleshooting

### Connection Testing
If the main app has issues, use the diagnostic tool:
```powershell
python simple_mcp_test.py
```
This tests your MCP server connection independently.

### Common Issues

**❌ "MCP connection failed"**
- Check that your MCP server command is correct
- Verify the server file exists and runs without errors
- Try running the server manually first: `python wifi_diagnostics_mcp.py`

**❌ "OpenAI API connection failed"**
- Verify your API key is correct
- Check your internet connection
- Ensure you have API credits available

**❌ "No tools found"**
- Your MCP server may not be exposing tools properly
- Check server logs for errors
- Verify the server implements MCP protocol correctly

**❌ ChatGPT not responding**
- Check the status bar for connection issues
- Look for error messages in red text
- Try restarting the application

**❌ Tools not working**
- Some tools require administrator privileges
- Check Windows Event Viewer for permission errors
- Run PowerShell as Administrator if needed

### Debug Information
The application prints helpful debug info to the console:
```
Status: OpenAI API connected successfully
MCP Init result: ...
Tools result: ...
Sending to GPT: hello
Tools available: 6
```

### Error Recovery
If something goes wrong:
1. **Close the application** (click X or Ctrl+C in terminal)
2. **Check the status messages** for specific errors
3. **Fix the underlying issue** (API key, MCP server, etc.)
4. **Restart the application**

## Advanced Usage

### Custom MCP Servers
Replace `wifi_diagnostics_mcp.py` with your own MCP server to give ChatGPT access to:
- Custom APIs and databases
- File system operations
- Hardware monitoring tools
- Business process automation
- Any Python/Node.js functionality

### Configuration Options
Edit `mcp_chatgpt_client.py` to customize:
- **Model Selection** - Change from GPT-4 to GPT-3.5-turbo (line 145)
- **Window Size** - Modify `geometry("800x600")` (line 306)
- **Tool Timeout** - Adjust subprocess timeout (line 30 in MCP server)

### Multiple MCP Servers
Currently supports one MCP server at a time. To use multiple:
1. Combine tools into a single MCP server
2. Or modify the client to support multiple connections
3. Or run multiple client instances

### Command Line Options
You can modify the startup to accept command line arguments:
- MCP server command
- API key override
- Debug verbosity levels

### Integration with Claude Desktop
This client complements Claude Desktop:
- Use Claude Desktop for development and testing
- Use this client for ChatGPT integration and demos
- Share the same MCP server between both

### Security Considerations
- Keep your OpenAI API key secure
- Be cautious with MCP tools that modify system settings
- Review tool permissions before granting administrator access
- Consider network security for tools that access external APIs

---

**Next Steps:**
- Try the [WiFi diagnostic example](wifi_diagnostic_prompt.md)
- Read the [Technical Documentation](TECHNICAL_DOCS.md)
- Explore [Examples and Use Cases](EXAMPLES.md)