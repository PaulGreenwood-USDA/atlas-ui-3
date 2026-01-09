# LLM Integration

Atlas UI 3 uses LiteLLM as a unified interface to multiple LLM providers.

## Configuration

LLM models are configured in `config/overrides/llmconfig.yml`:

```yaml
models:
  cerebras-gpt-oss-120b:
    model_url: "https://api.cerebras.ai/v1"
    model_name: "gpt-oss-120b"
    api_key: "${CEREBRAS_API_KEY}"
    compliance_level: "External"
    max_tokens: 10000
    temperature: 0.7

  openai-gpt-4:
    model_url: "https://api.openai.com/v1/chat/completions"
    model_name: "gpt-4"
    api_key: "${OPENAI_API_KEY}"
    compliance_level: "External"
```

### Configuration Fields

| Field | Required | Description |
|-------|----------|-------------|
| `model_url` | Yes | API endpoint URL |
| `model_name` | Yes | Model identifier for the provider |
| `api_key` | Yes | API key (use `${ENV_VAR}` syntax) |
| `compliance_level` | No | For compliance filtering (Internal/External) |
| `max_tokens` | No | Maximum output tokens (default: 1000) |
| `temperature` | No | Default temperature (default: 0.7) |
| `extra_headers` | No | Additional HTTP headers |

## LiteLLM Caller

The `LiteLLMCaller` class (`backend/modules/llm/litellm_caller.py`) provides the main interface:

### Methods

#### `call_plain(model_name, messages, temperature)`
Simple LLM call without tools.

```python
response = await llm_caller.call_plain(
    model_name="cerebras-gpt-oss-120b",
    messages=[{"role": "user", "content": "Hello"}],
    temperature=0.7
)
# Returns: str
```

#### `call_with_tools(model_name, messages, tools_schema, tool_choice, temperature)`
LLM call with function calling support.

```python
response = await llm_caller.call_with_tools(
    model_name="openai-gpt-4",
    messages=messages,
    tools_schema=tools_schema,
    tool_choice="auto",  # or "required"
    temperature=0.7
)
# Returns: LLMResponse with .content and .tool_calls
```

#### `call_with_rag(model_name, messages, data_sources, user_email, temperature)`
LLM call with RAG context injection.

#### `call_with_rag_and_tools(...)`
Combined RAG and tools support.

## LLMResponse

```python
@dataclass
class LLMResponse:
    content: str                    # Text response
    tool_calls: Optional[List]      # Tool calls if any
    model_used: str                 # Model that was used
    
    def has_tool_calls(self) -> bool:
        return bool(self.tool_calls)
```

## Provider Mapping

LiteLLM maps internal model names to provider-specific formats:

| URL Pattern | LiteLLM Format |
|-------------|----------------|
| `openrouter` | `openrouter/{model_id}` |
| `openai` | `openai/{model_id}` |
| `anthropic` | `anthropic/{model_id}` |
| `cerebras` | `cerebras/{model_id}` |
| `google` | `google/{model_id}` |

## Tool Call Parsing (Fallback)

Some models (like Cerebras) don't properly support native function calling and output tool calls as JSON in their text response. The `tool_call_parser` module handles this:

```python
# backend/modules/llm/tool_call_parser.py

# Automatically triggered when:
# 1. Model returns no tool_calls
# 2. Content contains JSON that looks like tool calls

# Supported formats:
{"name": "tool_name", "arguments": {...}}
{"function": "tool_name", "args": {...}}
{"tool": "tool_name", "parameters": {...}}
{"tool_name": {...}}  # Direct tool name as key
```

This happens automatically in `call_with_tools()`:

```python
if not tool_calls and should_attempt_content_parsing(content):
    parsed_tool_calls, cleaned_content = extract_tool_calls_from_content(
        content, available_tools
    )
```

## Adding a New Provider

1. **Update llmconfig.yml** with the new model configuration

2. **Add provider mapping** in `_get_litellm_model_name()`:
```python
elif "newprovider" in model_config.model_url:
    return f"newprovider/{model_id}"
```

3. **Set environment variable** for API key:
```python
elif "newprovider" in model_config.model_url:
    _set_env_var_if_needed("NEWPROVIDER_API_KEY", api_key)
```

4. **Update .env.example** with the new key placeholder

## Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `CEREBRAS_API_KEY` | Cerebras API key |
| `OPENROUTER_API_KEY` | OpenRouter API key |
| `GROQ_API_KEY` | Groq API key |
| `GOOGLE_API_KEY` | Google AI API key |

## Debugging

Enable verbose LiteLLM logging:

```bash
export LITELLM_LOG=DEBUG
```

Or check the application logs:

```bash
Get-Content logs/app.jsonl -Tail 50
```

## Error Handling

LLM errors are wrapped in domain errors:

```python
try:
    response = await llm_caller.call_with_tools(...)
except Exception as e:
    raise LLMError(f"Failed to call LLM: {e}")
```

See [Error Handling](error_handling_improvements.md) for UI error display.
