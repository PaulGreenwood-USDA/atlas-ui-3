# Configuration System

Atlas UI 3 uses a layered configuration system with support for environment variables, YAML, and JSON files.

## Configuration Layers

Configuration is loaded in priority order (highest first):

1. **Environment Variables** - Override everything
2. **`config/overrides/`** - Project-specific overrides
3. **`config/defaults/`** - Default values
4. **Legacy paths** - Backward compatibility

## Configuration Files

### Application Settings (.env)

Core application settings via environment variables:

```bash
# Server
HOST=127.0.0.1
PORT=8000
DEBUG_MODE=false

# Features
FEATURE_TOOLS_ENABLED=true
FEATURE_RAG_MCP_ENABLED=false
FEATURE_COMPLIANCE_LEVELS_ENABLED=false
FEATURE_AGENT_MODE_AVAILABLE=true

# Security
CAPABILITY_TOKEN_SECRET=your-secret-here
FILE_UPLOAD_MAX_SIZE_MB=50
```

### LLM Configuration (llmconfig.yml)

```yaml
# config/overrides/llmconfig.yml
models:
  model-name:
    model_url: "https://api.provider.com/v1"
    model_name: "provider-model-id"
    api_key: "${API_KEY_ENV_VAR}"
    max_tokens: 10000
    temperature: 0.7
    compliance_level: "External"
    extra_headers:
      Custom-Header: "value"
```

### MCP Configuration (mcp.json)

```json
{
  "servers": {
    "server-name": {
      "groups": ["default", "admin"],
      "command": ".venv/Scripts/python",
      "cwd": "backend/mcp/servername",
      "args": ["main.py"],
      "compliance_level": "Internal"
    }
  }
}
```

### RAG MCP Configuration (mcp-rag.json)

```json
{
  "servers": {
    "rag-server": {
      "groups": ["default"],
      "transport": "sse",
      "url": "http://localhost:9000/sse"
    }
  }
}
```

### Compliance Levels (compliance-levels.json)

```json
{
  "levels": {
    "Internal": {
      "description": "Internal use only",
      "allowed_with": ["Internal"]
    },
    "External": {
      "description": "External services",
      "allowed_with": ["Internal", "External"]
    }
  }
}
```

## ConfigManager

The `ConfigManager` class (`backend/modules/config/config_manager.py`) handles all configuration:

```python
from modules.config import config_manager

# Access LLM config
llm_config = config_manager.llm_config
models = llm_config.models

# Access MCP config  
mcp_config = config_manager.mcp_config
servers = mcp_config.servers

# Access app settings
app_settings = config_manager.app_settings
debug = app_settings.debug_mode
```

## AppSettings

Pydantic model for application settings:

```python
class AppSettings(BaseSettings):
    # Server
    host: str = "127.0.0.1"
    port: int = 8000
    debug_mode: bool = False
    
    # Features
    feature_tools_enabled: bool = False
    feature_rag_mcp_enabled: bool = False
    feature_compliance_levels_enabled: bool = False
    feature_agent_mode_available: bool = True
    
    # Security
    capability_token_secret: Optional[str] = None
    file_upload_max_size_mb: int = 50
    file_upload_allowed_extensions: str = ".pdf,.csv,.txt,..."
    
    # Agent
    agent_loop_strategy: str = "think-act"
    agent_max_steps: int = 30
```

## Environment Variable Resolution

Config values can reference environment variables:

```yaml
api_key: "${OPENAI_API_KEY}"
```

The `resolve_env_var()` function handles this:

```python
from modules.config.config_manager import resolve_env_var

value = resolve_env_var("${MY_VAR}")  # Resolves to env value
value = resolve_env_var("literal")     # Returns as-is
```

## Feature Flags

Control features via environment variables:

| Flag | Default | Description |
|------|---------|-------------|
| `FEATURE_TOOLS_ENABLED` | false | Enable MCP tools |
| `FEATURE_RAG_MCP_ENABLED` | false | Enable RAG over MCP |
| `FEATURE_COMPLIANCE_LEVELS_ENABLED` | false | Enable compliance filtering |
| `FEATURE_AGENT_MODE_AVAILABLE` | true | Allow agent mode in UI |

## Config API Endpoint

The `/api/config` endpoint exposes configuration to the frontend:

```json
{
  "models": [{"id": "model-name", "name": "Display Name", ...}],
  "tools": [{"server": "pdfbasic", "tools": [...]}],
  "prompts": [...],
  "data_sources": [...],
  "features": {
    "tools": true,
    "rag": false,
    "agent_mode": true
  }
}
```

## Configuration Best Practices

### 1. Use Environment Variables for Secrets

```bash
# .env
OPENAI_API_KEY=sk-...
CAPABILITY_TOKEN_SECRET=random-32-char-string
```

Never commit secrets to the repository.

### 2. Use Overrides for Project Settings

```yaml
# config/overrides/llmconfig.yml
models:
  my-model:
    api_key: "${MY_API_KEY}"  # Reference env var
```

### 3. Use Defaults for Shared Settings

```yaml
# config/defaults/llmconfig.yml
models:
  demo-model:
    # Safe defaults for development
```

### 4. Check Configuration on Startup

The application validates configuration on startup. Check logs for:

```
INFO: Loaded 3 models from llmconfig.yml
INFO: Loaded 5 MCP servers from mcp.json
WARNING: CAPABILITY_TOKEN_SECRET not set
```

## Testing Configuration

### Example Configs

Test configurations are in `config/mcp-example-configs/`:

```
config/mcp-example-configs/
├── mcp-pdfbasic.json
├── mcp-code-executor.json
└── mcp-web-search.json
```

### Overriding for Tests

```python
# In tests
import os
os.environ["FEATURE_TOOLS_ENABLED"] = "true"

# Or mock the config manager
from unittest.mock import patch, MagicMock

@patch('modules.config.config_manager.app_settings')
def test_something(mock_settings):
    mock_settings.feature_tools_enabled = True
    # ...
```

## Troubleshooting

### Config Not Loading
- Check file exists in `config/overrides/` or `config/defaults/`
- Verify YAML/JSON syntax
- Check `APP_CONFIG_OVERRIDES` and `APP_CONFIG_DEFAULTS` env vars

### Environment Variable Not Resolved
- Verify env var is set: `echo $MY_VAR`
- Check syntax: must be `${VAR_NAME}` exactly
- Restart backend after changing .env

### Feature Not Enabled
- Check feature flag in .env
- Restart backend after changes
- Verify via `/api/config` endpoint
