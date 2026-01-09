# Chat System Architecture

The chat system is the core of Atlas UI 3, orchestrating message handling, tool execution, and LLM interactions.

## Overview

```
User Message → WebSocket → ChatService → ChatOrchestrator → Mode Runner → LLM
                                              ↓
                              Tool Execution (if needed)
                                              ↓
                              Response → WebSocket → UI
```

## Key Components

### ChatService (`backend/application/chat/service.py`)

The main entry point for chat operations. Handles:
- Session management
- Message routing to the orchestrator
- Mode runner initialization

```python
# Key method signature
async def handle_chat_message(
    self,
    session_id: UUID,
    content: str,
    model: str,
    selected_tools: Optional[List[str]] = None,
    selected_prompts: Optional[List[str]] = None,
    selected_data_sources: Optional[List[str]] = None,
    agent_mode: bool = False,
    temperature: float = 0.7,
    ...
) -> Dict[str, Any]
```

### ChatOrchestrator (`backend/application/chat/orchestrator.py`)

Coordinates the full request flow:
1. Session retrieval
2. Message history building
3. File handling and tool suggestion
4. Mode selection and execution

**Mode Selection Logic:**
```python
if agent_mode:
    → AgentModeRunner
elif selected_tools:
    → ToolsModeRunner
elif selected_data_sources:
    → RagModeRunner
else:
    → PlainModeRunner
```

### Mode Runners

Located in `backend/application/chat/modes/`:

| Mode | File | Purpose |
|------|------|---------|
| Plain | `plain.py` | Simple LLM calls without tools |
| RAG | `rag.py` | LLM calls with RAG context |
| Tools | `tools.py` | LLM calls with tool execution |
| Agent | `agent.py` | Multi-step agent loops |

## Message Flow

### 1. WebSocket Reception

```python
# backend/main.py - WebSocket handler
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # ... connection handling
    data = await websocket.receive_json()
    if data["type"] == "chat":
        await chat_service.handle_chat_message(...)
```

### 2. Message Building

The `MessageBuilder` (`backend/application/chat/preprocessors/message_builder.py`) constructs the message array:

```python
messages = [
    {"role": "system", "content": system_prompt},
    {"role": "system", "content": files_manifest},  # if files attached
    # ... conversation history
    {"role": "user", "content": user_message}
]
```

### 3. LLM Calling

The `LiteLLMCaller` (`backend/modules/llm/litellm_caller.py`) handles all LLM interactions:

```python
# Plain call
response = await llm.call_plain(model, messages, temperature)

# Call with tools
response = await llm.call_with_tools(model, messages, tools_schema, tool_choice)
```

### 4. Tool Execution

When the LLM returns tool calls:

```python
# backend/application/chat/utilities/tool_utils.py
result = await execute_single_tool(
    tool_call=tool_call,
    session_context=context,
    tool_manager=tool_manager,
    update_callback=callback
)
```

## Auto Tool Suggestion

When files are attached, relevant tools are automatically suggested:

```python
# backend/application/chat/preprocessors/file_tool_suggester.py
FILE_TYPE_TOOL_PATTERNS = {
    ".pdf": ["pdf", "document", "extract_text"],
    ".csv": ["csv", "spreadsheet", "data"],
    ".png": ["image", "vision", "ocr"],
    # ...
}
```

This happens in the orchestrator before mode selection:

```python
effective_tools = self.file_tool_suggester.suggest_tools(
    files=files,
    user_selected_tools=selected_tools
)
```

## Event Publishing

The `EventPublisher` (`backend/infrastructure/events/publisher.py`) sends real-time updates:

```python
await event_publisher.publish_chat_response(message, has_pending_tools)
await event_publisher.publish_tool_start(tool_name, tool_call_id)
await event_publisher.publish_tool_result(tool_call_id, result)
await event_publisher.publish_response_complete()
```

## Session Management

Sessions store conversation state:

```python
# backend/domain/sessions/models.py
class Session:
    id: UUID
    history: ConversationHistory  # Message list
    context: Dict[str, Any]       # Files, metadata
    created_at: datetime
    updated_at: datetime
```

## Adding a New Chat Mode

1. Create a new runner in `backend/application/chat/modes/`:

```python
class CustomModeRunner:
    def __init__(self, llm, event_publisher, ...):
        self.llm = llm
        self.event_publisher = event_publisher
    
    async def run(self, session, model, messages, **kwargs):
        # Your custom logic
        response = await self.llm.call_plain(model, messages)
        
        await self.event_publisher.publish_chat_response(response)
        await self.event_publisher.publish_response_complete()
        
        return {"message": response}
```

2. Register in `ChatOrchestrator.__init__`
3. Add routing logic in `ChatOrchestrator.execute`

## Error Handling

Errors are classified and surfaced to the UI:

```python
# backend/domain/errors.py
class LLMError(DomainError): ...
class ToolExecutionError(DomainError): ...
class RateLimitError(DomainError): ...
```

See [Error Handling](error_handling_improvements.md) for details.
