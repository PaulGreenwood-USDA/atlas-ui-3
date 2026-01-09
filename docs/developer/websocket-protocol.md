# WebSocket Protocol

Atlas UI 3 uses WebSockets for real-time bidirectional communication between the frontend and backend.

## Connection

### Endpoint
```
ws://localhost:8000/ws
```

### Connection Flow
1. Frontend connects to `/ws`
2. Backend accepts connection
3. Both sides can send/receive JSON messages
4. Connection persists for the session

## Message Types

### Client → Server

#### Chat Message
```json
{
  "type": "chat",
  "content": "User message text",
  "model": "cerebras-gpt-oss-120b",
  "session_id": "uuid-string",
  "selected_tools": ["pdfbasic_extract_pdf_text"],
  "selected_prompts": [],
  "selected_data_sources": [],
  "agent_mode": false,
  "temperature": 0.7
}
```

#### File Attachment
```json
{
  "type": "attach_file",
  "session_id": "uuid-string",
  "file": {
    "name": "document.pdf",
    "content": "base64-encoded-content",
    "mime_type": "application/pdf"
  }
}
```

#### Session Reset
```json
{
  "type": "reset_session",
  "session_id": "uuid-string"
}
```

#### File Download Request
```json
{
  "type": "download_file",
  "file_key": "users/email/uploads/filename.pdf"
}
```

#### Tool Approval Response
```json
{
  "type": "tool_approval_response",
  "tool_call_id": "call_abc123",
  "approved": true
}
```

#### Elicitation Response
```json
{
  "type": "elicitation_response",
  "request_id": "elicit_xyz",
  "action": "accept",
  "data": {"field": "value"}
}
```

### Server → Client

#### Token Stream
Streamed response tokens:
```json
{
  "type": "token_stream",
  "content": "partial response text"
}
```

#### Chat Response
Complete response:
```json
{
  "type": "chat_response",
  "message": "Complete response text",
  "has_pending_tools": false
}
```

#### Response Complete
Signals end of response:
```json
{
  "type": "response_complete"
}
```

#### Tool Lifecycle Events

**Tool Start:**
```json
{
  "type": "tool_start",
  "tool_name": "pdfbasic_extract_pdf_text",
  "tool_call_id": "call_abc123",
  "server_name": "pdfbasic",
  "arguments": {"filename": "doc.pdf"}
}
```

**Tool Progress:**
```json
{
  "type": "tool_progress",
  "tool_call_id": "call_abc123",
  "progress": 50,
  "total": 100,
  "percentage": 50,
  "message": "Processing page 5 of 10"
}
```

**Tool Result:**
```json
{
  "type": "tool_result",
  "tool_call_id": "call_abc123",
  "success": true,
  "result": {"summary": "Extracted 5000 characters"}
}
```

**Tool Error:**
```json
{
  "type": "tool_error",
  "tool_call_id": "call_abc123",
  "error": "Failed to read PDF"
}
```

#### Tool Approval Request
```json
{
  "type": "tool_approval_request",
  "tool_call_id": "call_abc123",
  "tool_name": "code_executor_run_python",
  "arguments": {"code": "print('hello')"},
  "requires_approval": true
}
```

#### Elicitation Request
```json
{
  "type": "elicitation_request",
  "request_id": "elicit_xyz",
  "server_name": "myserver",
  "tool_name": "my_tool",
  "message": "Please provide input",
  "schema": {
    "type": "object",
    "properties": {
      "name": {"type": "string"}
    }
  }
}
```

#### Canvas Content
```json
{
  "type": "canvas_content",
  "content": "base64-content",
  "filename": "report.html",
  "mime_type": "text/html"
}
```

#### Intermediate Update
For agent mode reasoning:
```json
{
  "type": "intermediate_update",
  "step": 3,
  "reasoning": "Analyzing the document structure...",
  "action": "tool_call"
}
```

#### Error
```json
{
  "type": "error",
  "error": "Error message",
  "error_type": "LLMError",
  "details": {}
}
```

#### Session Files Update
```json
{
  "type": "session_files",
  "files": [
    {
      "name": "document.pdf",
      "key": "users/email/uploads/doc.pdf",
      "size": 12345,
      "mime_type": "application/pdf"
    }
  ]
}
```

## Frontend Handling

### WebSocket Context

```jsx
// frontend/src/contexts/WSContext.jsx
const { sendMessage, isConnected } = useWebSocket();

// Send a chat message
sendMessage({
  type: 'chat',
  content: 'Hello',
  model: selectedModel,
  session_id: sessionId,
  selected_tools: Array.from(selectedTools),
  // ...
});
```

### Message Handler

```jsx
// frontend/src/handlers/chat/websocketHandlers.js
export function createWebSocketHandler(deps) {
  return (data) => {
    switch (data.type) {
      case 'token_stream':
        // Append to current message
        break;
      case 'tool_start':
        // Show tool execution UI
        break;
      case 'tool_result':
        // Update tool status
        break;
      case 'error':
        // Show error notification
        break;
      // ...
    }
  };
}
```

## Backend Handling

### WebSocket Endpoint

```python
# backend/main.py
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data["type"] == "chat":
                await handle_chat_message(websocket, data)
            elif data["type"] == "reset_session":
                await handle_reset(websocket, data)
            # ...
    except WebSocketDisconnect:
        # Handle disconnect
        pass
```

### Sending Updates

```python
# Using the connection directly
await websocket.send_json({
    "type": "token_stream",
    "content": "Hello"
})

# Using EventPublisher
await event_publisher.publish_chat_response(
    message="Response text",
    has_pending_tools=False
)
```

## Connection Management

### Heartbeat
The connection is kept alive by the underlying WebSocket protocol. No explicit heartbeat is implemented.

### Reconnection
Frontend handles reconnection automatically on disconnect:

```jsx
useEffect(() => {
  if (!isConnected) {
    // Attempt reconnection
    connect();
  }
}, [isConnected]);
```

### Session Persistence
Sessions are identified by UUID and persist across reconnections.

## Error Handling

### Connection Errors
```jsx
// Frontend catches connection errors
websocket.onerror = (error) => {
  console.error('WebSocket error:', error);
  setIsConnected(false);
};
```

### Message Errors
```python
# Backend sends error messages
await websocket.send_json({
    "type": "error",
    "error": str(e),
    "error_type": type(e).__name__
})
```

## Debugging

### Browser DevTools
1. Open Network tab
2. Filter by "WS"
3. Click on the WebSocket connection
4. View Messages tab for all sent/received messages

### Backend Logging
```python
logger.debug(f"WebSocket received: {data['type']}")
logger.debug(f"WebSocket sending: {message['type']}")
```

## Best Practices

1. **Always include `type`** in all messages
2. **Use `session_id`** consistently across messages
3. **Handle disconnects gracefully** on both sides
4. **Don't block** the WebSocket with long operations
5. **Stream large responses** as token_stream events
