import asyncio
import json
import sys
import os
from typing import Dict, List, Any, Optional
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog
from datetime import datetime
import threading
import queue

# You'll need to install these dependencies:
# pip install openai mcp python-dotenv

try:
    import openai
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Missing required package: {e}")
    print("Please install with: pip install openai mcp python-dotenv")
    sys.exit(1)

# Load environment variables
load_dotenv()

class MCPChatGPTClient:
    def __init__(self):
        self.openai_client = None
        self.mcp_server_params = None
        self.mcp_tools = {}
        self.chat_history = []
        
        # GUI components
        self.root = None
        self.chat_display = None
        self.input_entry = None
        self.status_label = None
        
        # Threading
        self.message_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self.status_queue = queue.Queue()  # For status updates
        self.loop = None
        self.executor_thread = None
        
    async def initialize_mcp(self, server_command: List[str]):
        """Initialize MCP connection and get tool list"""
        try:
            self.status_queue.put("Connecting to MCP server...")
            
            self.mcp_server_params = StdioServerParameters(
                command=server_command[0],
                args=server_command[1:] if len(server_command) > 1 else []
            )
            
            # Test connection and get tools
            async with stdio_client(self.mcp_server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize the session
                    init_result = await session.initialize()
                    print(f"MCP Init result: {init_result}")
                    
                    # Get available tools
                    tools_result = await session.list_tools()
                    print(f"Tools result: {tools_result}")
                    self.mcp_tools = {tool.name: tool for tool in tools_result.tools}
            
            status_msg = f"MCP connected. Available tools: {', '.join(self.mcp_tools.keys())}"
            self.status_queue.put(status_msg)
            print(f"MCP Success: {status_msg}")
            return True
            
        except Exception as e:
            error_msg = f"MCP connection failed: {str(e)}"
            self.status_queue.put(error_msg)
            print(f"Full MCP error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def initialize_openai(self, api_key: str):
        """Initialize OpenAI client"""
        try:
            self.status_queue.put("Connecting to OpenAI API...")
            self.openai_client = openai.OpenAI(api_key=api_key)
            # Test the connection
            self.openai_client.models.list()
            self.status_queue.put("OpenAI API connected successfully")
            return True
        except Exception as e:
            error_msg = f"OpenAI API connection failed: {str(e)}"
            self.status_queue.put(error_msg)
            return False
    
    def mcp_tools_to_openai_format(self) -> List[Dict]:
        """Convert MCP tools to OpenAI function calling format"""
        openai_tools = []
        
        for tool_name, tool in self.mcp_tools.items():
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": tool.description,
                    "parameters": tool.inputSchema if hasattr(tool, 'inputSchema') else {"type": "object", "properties": {}}
                }
            }
            openai_tools.append(openai_tool)
        
        return openai_tools
    
    async def execute_mcp_tool(self, tool_name: str, arguments: Dict) -> str:
        """Execute an MCP tool and return the result"""
        try:
            # Create a new connection for each tool call
            async with stdio_client(self.mcp_server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize the session
                    await session.initialize()
                    
                    # Execute the tool
                    result = await session.call_tool(tool_name, arguments)
                    
                    # Format the result for display
                    if result.content:
                        content_parts = []
                        for content in result.content:
                            if hasattr(content, 'text'):
                                content_parts.append(content.text)
                            else:
                                content_parts.append(str(content))
                        return "\n".join(content_parts)
                    else:
                        return "Tool executed successfully (no output)"
                
        except Exception as e:
            return f"Error executing tool {tool_name}: {str(e)}"
    
    async def chat_with_gpt(self, message: str):
        """Send message to ChatGPT with MCP tools available"""
        try:
            self.chat_history.append({"role": "user", "content": message})
            
            # Prepare tools for OpenAI
            tools = self.mcp_tools_to_openai_format() if self.mcp_tools else None
            
            print(f"Sending to GPT: {message}")
            print(f"Tools available: {len(tools) if tools else 0}")
            
            # Make the API call
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=self.chat_history,
                tools=tools,
                tool_choice="auto" if tools else None
            )
            
            message_obj = response.choices[0].message
            
            # Handle tool calls
            if message_obj.tool_calls:
                self.chat_history.append(message_obj)
                
                for tool_call in message_obj.tool_calls:
                    tool_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)
                    
                    # Send tool call notification to GUI
                    self.response_queue.put(("tool", f"🔧 Calling tool: {tool_name} with {arguments}"))
                    
                    # Execute the MCP tool
                    tool_result = await self.execute_mcp_tool(tool_name, arguments)
                    
                    # Add tool result to conversation
                    self.chat_history.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "content": tool_result
                    })
                
                # Get final response after tool execution
                final_response = self.openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=self.chat_history
                )
                
                final_message = final_response.choices[0].message.content
                self.chat_history.append({"role": "assistant", "content": final_message})
                self.response_queue.put(("assistant", final_message))
                
            else:
                # Regular response without tools
                content = message_obj.content
                self.chat_history.append({"role": "assistant", "content": content})
                self.response_queue.put(("assistant", content))
                
        except Exception as e:
            error_msg = f"Error communicating with ChatGPT: {str(e)}"
            print(f"ChatGPT Error: {e}")
            import traceback
            traceback.print_exc()
            self.response_queue.put(("error", error_msg))
    
    async def async_worker(self):
        """Async worker thread that processes messages"""
        print("Async worker started")
        while True:
            try:
                # Check for new messages
                try:
                    message = self.message_queue.get_nowait()
                    if message == "QUIT":
                        break
                    print(f"Processing message: {message}")
                    await self.chat_with_gpt(message)
                except queue.Empty:
                    pass
                
                # Small delay to prevent busy waiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"Worker error: {e}")
                import traceback
                traceback.print_exc()
                self.response_queue.put(("error", f"Worker error: {str(e)}"))
    
    def display_message(self, message: str, sender: str):
        """Display message in the chat window"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if sender == "user":
            formatted = f"[{timestamp}] You: {message}\n\n"
            color = "blue"
        elif sender == "assistant":
            formatted = f"[{timestamp}] ChatGPT: {message}\n\n"
            color = "green"
        elif sender == "tool":
            formatted = f"[{timestamp}] {message}\n\n"
            color = "orange"
        else:  # error
            formatted = f"[{timestamp}] Error: {message}\n\n"
            color = "red"
        
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, formatted)
        self.chat_display.tag_add(sender, f"end-{len(formatted)}c", "end")
        self.chat_display.tag_config(sender, foreground=color)
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
    
    def update_status(self, message: str):
        """Update status label"""
        if self.status_label:
            self.status_label.config(text=message)
        print(f"Status: {message}")
    
    def send_message_sync(self):
        """Send message to async worker"""
        message = self.input_entry.get().strip()
        if not message:
            return
        
        self.input_entry.delete(0, tk.END)
        self.display_message(message, "user")
        
        if not self.openai_client:
            self.display_message("OpenAI API not connected. Please check your API key.", "error")
            return
        
        # Send message to async worker
        print(f"Queuing message: {message}")
        self.message_queue.put(message)
    
    def on_enter_key(self, event):
        """Handle Enter key press"""
        self.send_message_sync()
    
    def check_responses(self):
        """Check for responses from async worker"""
        try:
            while True:
                sender, message = self.response_queue.get_nowait()
                self.display_message(message, sender)
        except queue.Empty:
            pass
        
        # Check for status updates
        try:
            while True:
                status_msg = self.status_queue.get_nowait()
                self.update_status(status_msg)
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.check_responses)
    
    def setup_gui(self):
        """Setup the GUI"""
        self.root = tk.Tk()
        self.root.title("MCP + ChatGPT Demo Client")
        self.root.geometry("800x600")
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Chat display
        self.chat_display = scrolledtext.ScrolledText(
            self.root, 
            wrap=tk.WORD, 
            width=80, 
            height=30,
            state=tk.DISABLED
        )
        self.chat_display.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Input frame
        input_frame = tk.Frame(self.root)
        input_frame.pack(padx=10, pady=(0, 10), fill=tk.X)
        
        self.input_entry = tk.Entry(input_frame, width=70)
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.input_entry.bind("<Return>", self.on_enter_key)
        
        send_button = tk.Button(
            input_frame, 
            text="Send", 
            command=self.send_message_sync
        )
        send_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Status bar
        self.status_label = tk.Label(
            self.root, 
            text="Starting up...", 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Welcome message
        welcome_msg = """Welcome to MCP + ChatGPT Demo Client!

This client connects your MCP server to ChatGPT, allowing ChatGPT to use your MCP tools.

Setup required:
1. Set OPENAI_API_KEY environment variable or .env file
2. Configure your MCP server command below
3. Start chatting!

Available MCP tools will be listed once connected.
"""
        self.display_message(welcome_msg, "assistant")
    
    def on_closing(self):
        """Handle window closing"""
        print("Shutting down...")
        self.message_queue.put("QUIT")
        if self.executor_thread and self.executor_thread.is_alive():
            self.executor_thread.join(timeout=2)
        self.root.destroy()
    
    def start_async_worker(self):
        """Start the async worker thread"""
        def run_async_worker():
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.async_worker())
            finally:
                loop.close()
        
        self.executor_thread = threading.Thread(target=run_async_worker, daemon=True)
        self.executor_thread.start()
        print("Async worker thread started")
    
    async def async_setup(self):
        """Handle async initialization"""
        # Get OpenAI API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            self.status_queue.put("Waiting for API key...")
            # We'll need to handle this in GUI thread since simpledialog needs main thread
            return False
        
        # Initialize OpenAI
        if not self.initialize_openai(api_key):
            return False
        
        # Get MCP server command - this also needs to be in GUI thread
        return True
    
    def complete_setup(self):
        """Complete setup in GUI thread"""
        try:
            # Get OpenAI API key if not set
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                api_key = simpledialog.askstring(
                    "OpenAI API Key", 
                    "Enter your OpenAI API Key:",
                    show='*'
                )
                if not api_key:
                    messagebox.showerror("Error", "OpenAI API key is required")
                    return
            
            # Initialize OpenAI in separate thread
            def init_openai():
                if self.initialize_openai(api_key):
                    # Get MCP server command
                    self.root.after(0, self.get_mcp_command)
                else:
                    self.status_queue.put("Failed to connect to OpenAI")
            
            threading.Thread(target=init_openai, daemon=True).start()
            
        except Exception as e:
            self.update_status(f"Setup error: {e}")
    
    def get_mcp_command(self):
        """Get MCP server command in GUI thread"""
        try:
            default_command = "python wifi_diagnostics_mcp.py"
            server_command = simpledialog.askstring(
                "MCP Server Command",
                "Enter the command to start your MCP server:",
                initialvalue=default_command
            )
            
            if server_command:
                # Initialize MCP connection in separate thread
                def init_mcp():
                    command_parts = server_command.split()
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        success = loop.run_until_complete(self.initialize_mcp(command_parts))
                        if success:
                            self.status_queue.put("🎉 Ready! You can now chat with ChatGPT using MCP tools.")
                        else:
                            self.status_queue.put("⚠️ ChatGPT ready, but MCP tools unavailable")
                    finally:
                        loop.close()
                
                threading.Thread(target=init_mcp, daemon=True).start()
            else:
                self.status_queue.put("⚠️ ChatGPT ready (no MCP tools)")
                
        except Exception as e:
            self.status_queue.put(f"MCP setup error: {e}")
    
    def run(self):
        """Run the application"""
        # Set up the GUI first
        self.setup_gui()
        
        # Start async worker
        self.start_async_worker()
        
        # Start response checker
        self.root.after(100, self.check_responses)
        
        # Start setup after GUI is ready
        self.root.after(1000, self.complete_setup)  # 1 second delay
        
        # Start the tkinter main loop
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.on_closing()

def main():
    # Handle the event loop for Windows
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    client = MCPChatGPTClient()
    client.run()

if __name__ == "__main__":
    main()