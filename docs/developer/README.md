# Developer's Guide

Technical documentation for developers working on Atlas UI 3.

## Quick Start

```bash
# Install uv (if not installed)
# See: https://github.com/astral-sh/uv

# Setup environment
uv venv && source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uv pip install -r requirements.txt

# Build frontend
cd frontend && npm install && npm run build && cd ..

# Start backend
cd backend && python main.py
```

Open http://localhost:8000

---

## Architecture

- [Architecture Overview](architecture.md) - High-level system design and component relationships
- [Chat System](chat-system.md) - Message handling, orchestration, and streaming
- [Tool System](tool-system.md) - MCP tools, execution, and auto-selection
- [LLM Integration](llm-integration.md) - LiteLLM configuration and provider support
- [Agent Mode](agent-mode.md) - Multi-step autonomous execution strategies
- [WebSocket Protocol](websocket-protocol.md) - Real-time client-server communication

## Configuration

- [Configuration System](configuration.md) - Config files, environment variables, and feature flags

## Building Features

### MCP Servers (Tools)
- [Creating MCP Servers](creating-mcp-servers.md) - Build custom tools
- [MCP Server Logging](mcp-server-logging.md) - Logging best practices
- [Progress Updates](progress-updates.md) - Streaming progress to UI
- [Elicitation](elicitation.md) - Request user input from tools

### Frontend Development
- [Canvas Renderers](canvas-renderers.md) - File display and viewers
- [Error Handling Improvements](error_handling_improvements.md) - LLM error classification and surfacing
- [Error Flow Diagram](error_flow_diagram.md) - End-to-end error flow diagram
- [Working with Files](working-with-files.md) - File upload and management

## Development

### Conventions
- [Development Conventions](conventions.md) - Code style and practices

### Testing
- [Testing Guide](testing.md) - Unit, integration, and E2E tests

### Documentation
- [Documentation Bundling](documentation-bundling.md) - Automated documentation bundling for CI/CD

---

## Key Files

### Backend
| File | Purpose |
|------|---------|
| `backend/main.py` | Application entry point |
| `backend/application/chat/service.py` | Core chat service |
| `backend/application/chat/orchestrator.py` | Request orchestration |
| `backend/modules/llm/litellm_caller.py` | LLM interface |
| `backend/modules/mcp_tools/client.py` | Tool manager |
| `backend/modules/config/config_manager.py` | Configuration |

### Frontend
| File | Purpose |
|------|---------|
| `frontend/src/App.jsx` | Main application |
| `frontend/src/contexts/ChatContext.jsx` | Chat state |
| `frontend/src/contexts/WSContext.jsx` | WebSocket connection |
| `frontend/src/handlers/chat/` | Message handlers |

### Configuration
| File | Purpose |
|------|---------|
| `.env` | Environment variables |
| `config/overrides/llmconfig.yml` | LLM models |
| `config/overrides/mcp.json` | MCP servers |

---

## Common Tasks

### Add a New LLM Model

1. Add config to `config/overrides/llmconfig.yml`
2. Set API key in `.env`
3. Restart backend

### Add a New Tool

1. Create server in `backend/mcp/`
2. Register in `config/overrides/mcp.json`
3. Restart backend

### Add a New Feature Flag

1. Add to `AppSettings` in `config_manager.py`
2. Add to `.env.example`
3. Use in code via `app_settings.feature_name`

### Debug an Issue

1. Set `DEBUG_MODE=true` in `.env`
2. Check `logs/app.jsonl`
3. Use browser DevTools for frontend/WebSocket

---

## Troubleshooting

### Backend won't start
- Check Python version (3.10+)
- Verify dependencies: `uv pip install -r requirements.txt`
- Check for port conflicts on 8000

### Frontend not loading
- Run `npm run build` in frontend/
- Never use `npm run dev`
- Check browser console for errors

### Tools not appearing
- Verify `FEATURE_TOOLS_ENABLED=true`
- Check `mcp.json` syntax
- Check user has access to tool groups

### WebSocket disconnects
- Check backend is running
- Look for errors in browser console
- Verify no proxy/firewall issues
