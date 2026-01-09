"""
Tests for the tool call parser module.
"""

import pytest
from modules.llm.tool_call_parser import (
    extract_json_blocks,
    parse_tool_call_from_json,
    extract_tool_calls_from_content,
    should_attempt_content_parsing,
    _find_matching_tool,
)


class TestExtractJsonBlocks:
    """Tests for extract_json_blocks function."""
    
    def test_single_json_block(self):
        content = 'Some text {"key": "value"} more text'
        blocks = extract_json_blocks(content)
        assert len(blocks) == 1
        assert blocks[0][0] == '{"key": "value"}'
    
    def test_multiple_json_blocks(self):
        content = '{"a": 1} text {"b": 2}'
        blocks = extract_json_blocks(content)
        assert len(blocks) == 2
        assert blocks[0][0] == '{"a": 1}'
        assert blocks[1][0] == '{"b": 2}'
    
    def test_nested_json(self):
        content = '{"outer": {"inner": "value"}}'
        blocks = extract_json_blocks(content)
        assert len(blocks) == 1
        assert blocks[0][0] == '{"outer": {"inner": "value"}}'
    
    def test_json_with_escaped_quotes(self):
        content = '{"key": "value with \\"quotes\\""}'
        blocks = extract_json_blocks(content)
        assert len(blocks) == 1
    
    def test_no_json(self):
        content = 'Just plain text without JSON'
        blocks = extract_json_blocks(content)
        assert len(blocks) == 0


class TestParseToolCallFromJson:
    """Tests for parse_tool_call_from_json function."""
    
    def test_openai_format(self):
        json_obj = {"name": "my_tool", "arguments": {"param1": "value1"}}
        result = parse_tool_call_from_json(json_obj)
        assert result is not None
        assert result["function"]["name"] == "my_tool"
        assert '"param1"' in result["function"]["arguments"]
    
    def test_function_format(self):
        json_obj = {"function": "my_tool", "args": {"param1": "value1"}}
        result = parse_tool_call_from_json(json_obj)
        assert result is not None
        assert result["function"]["name"] == "my_tool"
    
    def test_tool_format(self):
        json_obj = {"tool": "my_tool", "parameters": {"param1": "value1"}}
        result = parse_tool_call_from_json(json_obj)
        assert result is not None
        assert result["function"]["name"] == "my_tool"
    
    def test_cmd_format_without_executor(self):
        json_obj = {"cmd": ["bash", "-lc", "ls -R"]}
        result = parse_tool_call_from_json(json_obj, available_tools=["pdf_tool"])
        # Should return None since no code executor is available
        assert result is None
    
    def test_direct_tool_name_as_key(self):
        json_obj = {"pdfbasic_extract_pdf_text": {"file_path": "/tmp/file.pdf"}}
        result = parse_tool_call_from_json(
            json_obj, 
            available_tools=["pdfbasic_extract_pdf_text", "pdfbasic_analyze_pdf"]
        )
        assert result is not None
        assert result["function"]["name"] == "pdfbasic_extract_pdf_text"
    
    def test_partial_tool_match(self):
        json_obj = {"extract_pdf": {"file_path": "/tmp/file.pdf"}}
        result = parse_tool_call_from_json(
            json_obj, 
            available_tools=["pdfbasic_extract_pdf_text", "pdfbasic_analyze_pdf"]
        )
        assert result is not None
        # Should match pdfbasic_extract_pdf_text due to partial match
        assert "extract" in result["function"]["name"].lower()


class TestFindMatchingTool:
    """Tests for _find_matching_tool function."""
    
    def test_exact_match(self):
        result = _find_matching_tool("my_tool", ["my_tool", "other_tool"])
        assert result == "my_tool"
    
    def test_case_insensitive(self):
        result = _find_matching_tool("MY_TOOL", ["my_tool", "other_tool"])
        assert result == "my_tool"
    
    def test_partial_match(self):
        result = _find_matching_tool("extract_pdf", ["pdfbasic_extract_pdf_text"])
        assert result == "pdfbasic_extract_pdf_text"
    
    def test_no_match(self):
        result = _find_matching_tool("unknown", ["tool_a", "tool_b"])
        assert result is None


class TestExtractToolCallsFromContent:
    """Tests for extract_tool_calls_from_content function."""
    
    def test_extracts_tool_call(self):
        content = 'Let me use a tool {"name": "my_tool", "arguments": {"x": 1}} to help.'
        tool_calls, cleaned = extract_tool_calls_from_content(content)
        assert len(tool_calls) == 1
        assert tool_calls[0]["function"]["name"] == "my_tool"
        assert "my_tool" not in cleaned
    
    def test_multiple_tool_calls(self):
        content = '{"name": "tool1", "arguments": {}} and {"name": "tool2", "arguments": {}}'
        tool_calls, cleaned = extract_tool_calls_from_content(content)
        assert len(tool_calls) == 2
    
    def test_no_tool_calls(self):
        content = 'Just regular text without tool calls'
        tool_calls, cleaned = extract_tool_calls_from_content(content)
        assert len(tool_calls) == 0
        assert cleaned == content
    
    def test_filters_unknown_json(self):
        content = '{"random": "data"} is not a tool call'
        tool_calls, cleaned = extract_tool_calls_from_content(content)
        # Random JSON that doesn't look like a tool call should be ignored
        assert len(tool_calls) == 0


class TestShouldAttemptContentParsing:
    """Tests for should_attempt_content_parsing function."""
    
    def test_with_json_indicators(self):
        assert should_attempt_content_parsing('{"cmd": ["bash"]}')
        assert should_attempt_content_parsing('Using {"name": "tool"}')
        assert should_attempt_content_parsing('{"function": "test"}')
    
    def test_without_json(self):
        assert not should_attempt_content_parsing('Plain text')
        assert not should_attempt_content_parsing('')
        assert not should_attempt_content_parsing(None)
    
    def test_json_without_tool_indicators(self):
        # Has JSON but no tool-like structure
        assert not should_attempt_content_parsing('{"user": "john", "age": 30}')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
