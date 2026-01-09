# Agent Mode

Agent mode enables multi-step autonomous task execution, where the LLM can reason, plan, and execute multiple tool calls to complete complex tasks.

## Overview

Unlike single-turn tool mode, agent mode:
- Executes multiple steps iteratively
- Maintains reasoning context across steps
- Can observe results and adapt strategy
- Continues until task completion or max steps

## Agent Loop Strategies

Three strategies are available (set via `AGENT_LOOP_STRATEGY`):

### 1. Think-Act (Default)

Alternates between thinking and acting:

```
Think → Act → Observe → Think → Act → Observe → ... → Final Answer
```

**Flow:**
1. LLM thinks about what to do
2. LLM selects a tool to call
3. Tool executes, result observed
4. Repeat until done

**Best for:** Complex tasks requiring deliberate reasoning

### 2. ReAct

Reason and Act in a structured format:

```
Thought: I need to analyze the PDF
Action: pdfbasic_extract_pdf_text
Observation: [tool result]
Thought: Now I should summarize...
```

**Flow:**
1. LLM produces Thought
2. LLM produces Action (tool call)
3. System adds Observation (tool result)
4. Repeat

**Best for:** Tasks requiring explicit reasoning traces

### 3. Act

Direct action without explicit reasoning:

```
Action → Observe → Action → Observe → ... → Answer
```

**Flow:**
1. LLM directly selects tools
2. Execute and observe
3. Repeat

**Best for:** Simple multi-step tasks

## Configuration

### Environment Variables

```bash
# Enable agent mode in UI
FEATURE_AGENT_MODE_AVAILABLE=true

# Default strategy
AGENT_LOOP_STRATEGY=think-act

# Maximum steps before forcing completion
AGENT_MAX_STEPS=30
```

### Per-Request Override

```json
{
  "type": "chat",
  "agent_mode": true,
  "agent_loop_strategy": "react",
  "agent_max_steps": 20
}
```

## Implementation

### AgentModeRunner

Located in `backend/application/chat/modes/agent.py`:

```python
class AgentModeRunner:
    def __init__(self, agent_loop_factory, ...):
        self.agent_loop_factory = agent_loop_factory
    
    async def run(self, session, model, messages, selected_tools, ...):
        # Create appropriate loop based on strategy
        agent_loop = self.agent_loop_factory.create(strategy)
        
        # Run the agent loop
        result = await agent_loop.run(
            model=model,
            messages=messages,
            context=context,
            selected_tools=selected_tools,
            max_steps=max_steps,
            event_handler=event_handler
        )
        
        return result
```

### Agent Loops

Located in `backend/application/chat/agent/`:

| File | Class | Strategy |
|------|-------|----------|
| `think_act_loop.py` | `ThinkActAgentLoop` | think-act |
| `react_loop.py` | `ReActAgentLoop` | react |
| `act_loop.py` | `ActAgentLoop` | act |

### AgentContext

```python
@dataclass
class AgentContext:
    session_id: UUID
    user_email: str
    files: Dict[str, Any]
    conversation_history: List[Dict]
```

### AgentResult

```python
@dataclass
class AgentResult:
    final_answer: str
    steps_taken: int
    tool_calls_made: List[str]
    reasoning_trace: List[str]
```

## Event Flow

Agent mode sends intermediate updates to the UI:

```python
# Step start
await event_handler.on_step_start(step_number, "thinking")

# Reasoning
await event_handler.on_reasoning(thought_text)

# Tool selection
await event_handler.on_tool_selected(tool_name, arguments)

# Tool result
await event_handler.on_tool_result(tool_name, result)

# Step complete
await event_handler.on_step_complete(step_number)

# Final answer
await event_handler.on_final_answer(answer)
```

### WebSocket Messages

**Intermediate Update:**
```json
{
  "type": "intermediate_update",
  "step": 3,
  "phase": "thinking",
  "reasoning": "I need to extract the PDF text first...",
  "action": null
}
```

**Tool Selection:**
```json
{
  "type": "intermediate_update", 
  "step": 3,
  "phase": "acting",
  "reasoning": null,
  "action": {
    "tool": "pdfbasic_extract_pdf_text",
    "arguments": {"filename": "doc.pdf"}
  }
}
```

## Prompts

Agent prompts are in `prompts/`:

| File | Purpose |
|------|---------|
| `agent_system_prompt.md` | Main agent instructions |
| `agent_observe_prompt.md` | Observation formatting |
| `agent_reason_prompt.md` | Reasoning instructions |
| `agent_summary_prompt.md` | Final answer generation |

## Safety Features

### Max Steps Limit

Prevents infinite loops:

```python
if step >= max_steps:
    logger.warning(f"Agent reached max steps ({max_steps})")
    final_answer = await self._force_final_answer(messages)
    break
```

### Consecutive Think Limit

Forces action if model keeps thinking without acting:

```python
if consecutive_thinks >= 3:
    logger.warning("Too many consecutive thinks, forcing action")
    # Add guidance to select a tool
```

### Finish Flag Fallback

Some models don't set `finish: true` properly:

```python
# Check for final_answer without finish flag
if "final_answer" in content.lower() and not has_tool_calls:
    logger.info("Detected final_answer without finish flag")
    break
```

## Frontend UI

Agent mode displays:
1. Current step number
2. Thinking/Acting phase
3. Reasoning text (collapsible)
4. Tool calls with results
5. Final answer

```jsx
// frontend/src/components/AgentSteps.jsx
{agentSteps.map((step, i) => (
  <AgentStep
    key={i}
    stepNumber={i + 1}
    phase={step.phase}
    reasoning={step.reasoning}
    toolCall={step.toolCall}
    result={step.result}
  />
))}
```

## Debugging

### Enable Verbose Logging

```bash
DEBUG_MODE=true
LOG_LEVEL=DEBUG
```

### Check Agent Logs

```bash
Get-Content logs/app.jsonl -Tail 100 | Select-String "agent|step|think|act"
```

### Common Issues

**Agent loops forever:**
- Check max_steps setting
- Verify finish detection
- Check tool results are meaningful

**Agent doesn't use tools:**
- Ensure tools are selected
- Check tool schemas are valid
- Verify agent prompt includes tool instructions

**Agent gives up too early:**
- Check for errors in tool execution
- Verify LLM understands the task
- May need more context in prompt

## Example Usage

```python
# Send agent mode request
{
  "type": "chat",
  "content": "Analyze this PDF and create a summary report",
  "model": "gpt-4",
  "agent_mode": true,
  "selected_tools": [
    "pdfbasic_extract_pdf_text",
    "canvas_canvas"
  ],
  "session_id": "..."
}
```

**Agent execution:**
1. Think: "I need to extract the PDF text"
2. Act: `pdfbasic_extract_pdf_text(filename="doc.pdf")`
3. Observe: [extracted text]
4. Think: "Now I'll summarize the key points"
5. Act: `canvas_canvas(content="# Summary\n...")`
6. Final: "I've created a summary in the canvas"
