"""
Tool call parser for models that don't support native function calling.

Some models (like Cerebras) output tool calls as JSON in their text content
instead of using the proper tool_calls response format. This module provides
utilities to extract and parse those embedded tool calls.
"""

import json
import logging
import re
import uuid
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def extract_json_blocks(content: str) -> List[Tuple[str, int, int]]:
    """
    Extract JSON blocks from text content.
    
    Returns list of (json_string, start_pos, end_pos) tuples.
    """
    blocks = []
    i = 0
    while i < len(content):
        if content[i] == '{':
            # Try to find matching closing brace
            depth = 0
            start = i
            in_string = False
            escape_next = False
            
            for j in range(i, len(content)):
                char = content[j]
                
                if escape_next:
                    escape_next = False
                    continue
                    
                if char == '\\' and in_string:
                    escape_next = True
                    continue
                    
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                    
                if in_string:
                    continue
                    
                if char == '{':
                    depth += 1
                elif char == '}':
                    depth -= 1
                    if depth == 0:
                        json_str = content[start:j+1]
                        blocks.append((json_str, start, j+1))
                        i = j
                        break
            else:
                # No matching brace found
                pass
        i += 1
    
    return blocks


def parse_tool_call_from_json(
    json_obj: Dict[str, Any],
    available_tools: Optional[List[str]] = None
) -> Optional[Dict[str, Any]]:
    """
    Try to parse a JSON object as a tool call.
    
    Handles various formats that models might use:
    - {"name": "tool_name", "arguments": {...}}
    - {"function": "tool_name", "args": {...}}
    - {"tool": "tool_name", "parameters": {...}}
    - {"tool_name": {...}} where tool_name is a known tool
    - {"cmd": [...]} bash-style commands (maps to code executor if available)
    
    Returns tool call in OpenAI format or None if not parseable.
    """
    # Format 1: OpenAI-like format with name and arguments
    if "name" in json_obj:
        tool_name = json_obj.get("name")
        arguments = json_obj.get("arguments", json_obj.get("args", json_obj.get("parameters", {})))
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {"input": arguments}
        return _create_tool_call(tool_name, arguments, available_tools)
    
    # Format 2: function/args format
    if "function" in json_obj:
        tool_name = json_obj.get("function")
        arguments = json_obj.get("args", json_obj.get("arguments", json_obj.get("parameters", {})))
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {"input": arguments}
        return _create_tool_call(tool_name, arguments, available_tools)
    
    # Format 3: tool/parameters format
    if "tool" in json_obj:
        tool_name = json_obj.get("tool")
        arguments = json_obj.get("parameters", json_obj.get("args", json_obj.get("arguments", {})))
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {"input": arguments}
        return _create_tool_call(tool_name, arguments, available_tools)
    
    # Format 4: cmd format (bash commands) - map to code executor or ignore
    if "cmd" in json_obj:
        cmd = json_obj.get("cmd")
        if isinstance(cmd, list) and len(cmd) >= 1:
            # Check if code-executor is available
            if available_tools and any("code" in t.lower() or "execute" in t.lower() for t in available_tools):
                # Try to map to code executor
                code_tool = next((t for t in available_tools if "execute" in t.lower() and "python" in t.lower()), None)
                if code_tool:
                    # Convert bash command to a note about what was attempted
                    cmd_str = " ".join(cmd) if isinstance(cmd, list) else str(cmd)
                    return _create_tool_call(
                        code_tool,
                        {"code": f"# Model attempted bash command: {cmd_str}\nprint('Bash commands not supported. Use Python instead.')"},
                        available_tools
                    )
            # If no code executor, return None - can't execute bash
            logger.debug(f"Ignoring bash command attempt: {cmd}")
            return None
    
    # Format 5: Direct tool name as key (e.g., {"pdfbasic_extract_pdf_text": {...}})
    if available_tools:
        for key in json_obj:
            # Check if the key matches or partially matches an available tool
            matching_tool = _find_matching_tool(key, available_tools)
            if matching_tool:
                arguments = json_obj[key]
                if isinstance(arguments, str):
                    try:
                        arguments = json.loads(arguments)
                    except json.JSONDecodeError:
                        arguments = {"input": arguments}
                elif not isinstance(arguments, dict):
                    arguments = {"input": arguments}
                return _create_tool_call(matching_tool, arguments, available_tools)
    
    return None


def _find_matching_tool(name: str, available_tools: List[str]) -> Optional[str]:
    """Find a matching tool from available tools."""
    name_lower = name.lower().replace("-", "_").replace(" ", "_")
    
    # Exact match
    for tool in available_tools:
        if tool.lower() == name_lower:
            return tool
    
    # Partial match (tool name contains the search name or vice versa)
    for tool in available_tools:
        tool_lower = tool.lower()
        if name_lower in tool_lower or tool_lower in name_lower:
            return tool
    
    # Fuzzy match on tool name parts
    name_parts = set(name_lower.split("_"))
    for tool in available_tools:
        tool_parts = set(tool.lower().split("_"))
        # If significant overlap in name parts
        overlap = name_parts & tool_parts
        if len(overlap) >= min(2, len(name_parts)):
            return tool
    
    return None


def _create_tool_call(
    tool_name: str,
    arguments: Dict[str, Any],
    available_tools: Optional[List[str]] = None
) -> Optional[Dict[str, Any]]:
    """Create a tool call in OpenAI format."""
    if not tool_name:
        return None
    
    # Try to find the actual tool name if available_tools provided
    if available_tools:
        matched_tool = _find_matching_tool(tool_name, available_tools)
        if matched_tool:
            tool_name = matched_tool
        else:
            logger.warning(f"Tool '{tool_name}' not found in available tools: {available_tools}")
            # Still create the call - let the execution fail gracefully
    
    return {
        "type": "function",
        "id": f"call_{uuid.uuid4().hex[:8]}",
        "function": {
            "name": tool_name,
            "arguments": json.dumps(arguments) if isinstance(arguments, dict) else str(arguments)
        }
    }


def extract_tool_calls_from_content(
    content: str,
    available_tools: Optional[List[str]] = None
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Extract tool calls embedded in content text.
    
    Args:
        content: The text content that may contain JSON tool calls
        available_tools: Optional list of available tool names for matching
        
    Returns:
        Tuple of (list of tool calls, cleaned content with JSON removed)
    """
    if not content:
        return [], ""
    
    tool_calls = []
    json_blocks = extract_json_blocks(content)
    
    # Track positions to remove from content
    positions_to_remove = []
    
    for json_str, start, end in json_blocks:
        try:
            json_obj = json.loads(json_str)
            if isinstance(json_obj, dict):
                tool_call = parse_tool_call_from_json(json_obj, available_tools)
                if tool_call:
                    tool_calls.append(tool_call)
                    positions_to_remove.append((start, end))
                    logger.info(f"Extracted tool call from content: {tool_call['function']['name']}")
        except json.JSONDecodeError:
            continue
    
    # Remove JSON blocks from content (in reverse order to preserve positions)
    cleaned_content = content
    for start, end in reversed(positions_to_remove):
        cleaned_content = cleaned_content[:start] + cleaned_content[end:]
    
    # Clean up multiple spaces and newlines
    cleaned_content = re.sub(r'\s+', ' ', cleaned_content).strip()
    
    return tool_calls, cleaned_content


def should_attempt_content_parsing(content: str) -> bool:
    """
    Heuristic to determine if content might contain embedded tool calls.
    
    Returns True if the content has patterns that suggest tool call attempts.
    """
    if not content:
        return False
    
    # Check for JSON-like patterns
    if '{' not in content:
        return False
    
    # Check for common tool call indicators
    indicators = [
        '"cmd"',
        '"name"',
        '"function"',
        '"tool"',
        '"arguments"',
        '"args"',
        '"parameters"',
        'bash',
        'python',
        '-lc',  # Common in bash -lc commands
    ]
    
    content_lower = content.lower()
    return any(ind.lower() in content_lower for ind in indicators)
