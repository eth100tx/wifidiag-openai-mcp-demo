# MCP-ChatGPT Bridge Client

A Windows desktop application that connects your MCP (Model Context Protocol) server to ChatGPT, enabling ChatGPT to use your custom tools and functions.

## 🚀 Quick Start

### Prerequisites
- Windows 10/11
- Python 3.8+
- OpenAI API key
- A working MCP server

### Installation
1. **Clone or download** this directory to your local machine
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Set up your OpenAI API key:**
   - Copy `.env.template` to `.env`
   - Add your API key: `OPENAI_API_KEY=your_key_here`
4. **Run the client:**
   ```bash
   python mcp_chatgpt_client.py
   ```

### First Run
1. The app will prompt for your OpenAI API key (if not in `.env`)
2. Enter your MCP server command (default: `python wifi_diagnostics_mcp.py`)
3. Wait for "🎉 Ready!" status
4. Start chatting with ChatGPT - it can now use your MCP tools!

## 📁 Files Overview

| File | Purpose |
|------|---------|
| `mcp_chatgpt_client.py` | Main application - GUI chat client |
| `wifi_diagnostics_mcp.py` | Example MCP server for WiFi diagnostics |
| `wifi_diagnostic_prompt.md` | Ready-to-use prompt for comprehensive WiFi troubleshooting |
| `simple_mcp_test.py` | Connection testing utility |
| `requirements.txt` | Python dependencies |
| `.env` | Your OpenAI API key (create from template) |

## 🎯 Example Use Cases

### WiFi Troubleshooting
Paste the content from `wifi_diagnostic_prompt.md` to get ChatGPT to run a complete WiFi diagnostic using your MCP tools.

### Custom Tools
Replace `wifi_diagnostics_mcp.py` with your own MCP server to give ChatGPT access to your custom tools and APIs.

## 🔧 Troubleshooting

**Connection Issues?**
```bash
python simple_mcp_test.py
```
This will test your MCP server connection independently.

**Common Problems:**
- **\"MCP connection failed\"** - Check that your MCP server command is correct
- **\"No tools found\"** - Verify your MCP server is properly configured
- **\"OpenAI API failed\"** - Check your API key in `.env` file

## 📚 Documentation

- **[User Guide](USER_GUIDE.md)** - Detailed setup and usage instructions
- **[Technical Docs](TECHNICAL_DOCS.md)** - Advanced configuration and development
- **[Examples](EXAMPLES.md)** - Sample interactions and use cases

## 🌟 Features

- ✅ **GUI Chat Interface** - Easy-to-use desktop chat application
- ✅ **MCP Integration** - Automatically exposes your MCP tools to ChatGPT
- ✅ **Tool Execution** - Real-time tool calling with progress display
- ✅ **Error Handling** - Robust error handling and debugging output
- ✅ **Multi-threading** - Responsive UI with background processing
- ✅ **Status Updates** - Clear connection and operation status

## 🎬 Demo

The included WiFi diagnostics server provides 6 tools that ChatGPT can use:
- `check_wifi_status` - Check adapter status and connections
- `diagnose_connection_issues` - Run connectivity tests
- `check_authentication_issues` - Analyze auth problems
- `analyze_wifi_environment` - Check signal and interference
- `generate_diagnostic_report` - Create comprehensive report
- `fix_common_issues` - Attempt automatic repairs

Ask ChatGPT: *\"Can you check my WiFi status and diagnose any issues?\"*

## 💡 Next Steps

1. **Try the WiFi diagnostics** - Use the included prompt for full testing
2. **Create your own MCP server** - Replace with tools for your use case
3. **Customize the client** - Modify the GUI or add features
4. **Share your tools** - Let ChatGPT use your APIs and automations

---

**Need help?** Check the [User Guide](USER_GUIDE.md) or [Technical Documentation](TECHNICAL_DOCS.md)