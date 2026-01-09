# Tool System

The tool system enables the LLM to execute actions through MCP (Model Context Protocol) servers.

## Architecture

```
LLM Response (tool_calls)
        ↓
    MCPToolManager
        ↓
    FastMCP Client
        ↓
    MCP Server (subprocess/HTTP)
        ↓
    Tool Execution
        ↓
    Result → LLM for synthesis
```

## MCP Configuration

Tools are configured in `config/overrides/mcp.json`:

```json
{
  "servers": {
    "pdfbasic": {
      "groups": ["default"],
      "command": ".venv/Scripts/python",
      "cwd": "backend/mcp/pdfbasic",
      "args": ["main.py"],
      "compliance_level": "Internal"
    },
    "external-api": {
      "groups": ["api-users"],
      "transport": "sse",
      "url": "https://api.example.com/mcp",
      "compliance_level": "External"
    }
  }
}
```

### Server Configuration Fields

| Field | Description |
|-------|-------------|
| `groups` | User groups that can access this server |
| `command` | Executable for stdio transport |
| `cwd` | Working directory |
| `args` | Command line arguments |
| `transport` | Transport type: `stdio` (default) or `sse`/`http` |
| `url` | URL for HTTP/SSE transport |
| `compliance_level` | For compliance filtering |

### Transport Detection

The system auto-detects transport based on configuration:
1. Explicit `transport` field
2. `command` present → stdio
3. `url` present → HTTP/SSE based on protocol

## MCPToolManager

Located in `backend/modules/mcp_tools/client.py`, manages all tool operations:

### Key Methods

```python
# Get available tools
tools = tool_manager.get_available_tools()
# Returns: ["pdfbasic_analyze_pdf", "pdfbasic_extract_pdf_text", ...]

# Get tool schemas for LLM
schemas = tool_manager.get_tools_schema(["pdfbasic_extract_pdf_text"])
# Returns: OpenAI function calling format

# Execute a tool
result = await tool_manager.execute_tool(tool_call, context)
# Returns: ToolResult
```

### Tool Naming Convention

Tools are namespaced with their server name:
```
{server_name}_{tool_name}
```

Example: `pdfbasic_extract_pdf_text`

## Tool Execution Flow

### 1. Schema Resolution

```python
# backend/application/chat/utilities/error_utils.py
tools_schema = await safe_get_tools_schema(tool_manager, selected_tools)
```

### 2. LLM Call with Tools

```python
response = await llm.call_with_tools(
    model=model,
    messages=messages,
    tools_schema=tools_schema,
    tool_choice="auto"
)
```

### 3. Tool Execution

```python
# backend/application/chat/utilities/tool_utils.py
async def execute_single_tool(
    tool_call,
    session_context,
    tool_manager,
    update_callback,
    config_manager
) -> ToolResult:
    # 1. Prepare arguments (inject file URLs, user info)
    prepared_args = prepare_tool_arguments(...)
    
    # 2. Send tool_start event to UI
    await update_callback({"type": "tool_start", ...})
    
    # 3. Execute via tool_manager
    result = await tool_manager.execute_tool(tool_call, context)
    
    # 4. Send tool_result event
    await update_callback({"type": "tool_result", ...})
    
    return result
```

### 4. Synthesis

After tool execution, results are sent back to the LLM for synthesis:

```python
messages.append({
    "role": "tool",
    "content": result.content,
    "tool_call_id": result.tool_call_id
})

final_response = await llm.call_plain(model, messages)
```

## Tool Result Format (V2 Contract)

Tools should return a dictionary with:

```python
{
    "results": {
        # Primary result data - shown in chat
        "summary": "Operation completed successfully",
        "data": {...}
    },
    "artifacts": [
        # Generated files - displayed in canvas
        {
            "name": "report.pdf",
            "b64": "base64_content",
            "mime": "application/pdf"
        }
    ],
    "display": {
        # UI hints
        "open_canvas": True,
        "primary_file": "report.pdf"
    }
}
```

## Auto Tool Selection

When files are attached, relevant tools are auto-selected:

```python
# backend/application/chat/preprocessors/file_tool_suggester.py
FILE_TYPE_TOOL_PATTERNS = {
    ".pdf": ["pdf", "document", "extract_text"],
    ".csv": ["csv", "spreadsheet", "data"],
    ".png": ["image", "vision", "ocr"],
    ...
}
```

This ensures users don't need to manually select PDF tools when attaching a PDF.

## Tool Authorization

Tools are filtered by user groups:

```python
# backend/application/chat/policies/tool_authorization.py
authorized_tools = await tool_authorization.filter_authorized_tools(
    selected_tools=tools,
    user_email=user_email
)
```

A user can only access tools from servers whose `groups` include at least one of the user's groups.

## Creating a New Tool

### 1. Create Server Directory

```
backend/mcp/myserver/
├── main.py
└── requirements.txt (optional)
```

### 2. Implement Tool

```python
# backend/mcp/myserver/main.py
from fastmcp import FastMCP
from typing import Dict, Any

mcp = FastMCP(name="MyServer")

@mcp.tool
def my_tool(param: str) -> Dict[str, Any]:
    """
    Tool description for the LLM.
    
    This docstring becomes the tool's description in the schema.
    
    Args:
        param: Description of the parameter
        
    Returns:
        Result dictionary
    """
    return {
        "results": {"output": f"Processed: {param}"},
    }

if __name__ == "__main__":
    mcp.run()
```

### 3. Register in mcp.json

```json
{
  "servers": {
    "myserver": {
      "groups": ["default"],
      "command": ".venv/Scripts/python",
      "cwd": "backend/mcp/myserver",
      "args": ["main.py"]
    }
  }
}
```

### 4. Restart Backend

The server will be discovered on startup.

## Debugging Tools

### Check Available Tools

```bash
curl http://localhost:8000/api/config | jq '.tools'
```

### Server Logs

Check `logs/app.jsonl` for tool execution logs:

```bash
Get-Content logs/app.jsonl -Tail 100 | Select-String "tool"
```

### MCP Debug Script

```bash
python scripts/debug_mcp_servers.py
```

## Common Issues

### Tool Not Appearing
- Check mcp.json syntax
- Verify server starts without errors
- Check user has access to server's group

### Tool Execution Fails
- Check tool arguments in logs
- Verify file paths/URLs are accessible
- Check MCP server logs

### Tool Result Not Displayed
- Ensure result follows V2 contract
- Check `results` key is present
- For artifacts, verify base64 encoding

See [Creating MCP Servers](creating-mcp-servers.md) for detailed server creation guide.
