"""
Tests for file-based tool suggestion service.
"""

import pytest
from application.chat.preprocessors.file_tool_suggester import (
    get_file_extension,
    get_suggested_tools_for_files,
    merge_tool_selections,
    FileToolSuggester,
)


class TestGetFileExtension:
    """Tests for get_file_extension function."""
    
    def test_pdf_extension(self):
        assert get_file_extension("document.pdf") == ".pdf"
        assert get_file_extension("DOCUMENT.PDF") == ".pdf"
    
    def test_image_extensions(self):
        assert get_file_extension("photo.jpg") == ".jpg"
        assert get_file_extension("image.PNG") == ".png"
        assert get_file_extension("graphic.JPEG") == ".jpeg"
    
    def test_no_extension(self):
        assert get_file_extension("filename") == ""
    
    def test_multiple_dots(self):
        assert get_file_extension("file.backup.pdf") == ".pdf"
        assert get_file_extension("report.2024.01.csv") == ".csv"


class TestGetSuggestedToolsForFiles:
    """Tests for get_suggested_tools_for_files function."""
    
    def test_pdf_suggests_pdf_tools(self):
        files = {"document.pdf": {"size": 1000}}
        available_tools = [
            "pdfbasic_extract_pdf_text",
            "pdfbasic_analyze_pdf",
            "code_executor_run_python",
        ]
        
        suggested = get_suggested_tools_for_files(files, available_tools)
        
        assert "pdfbasic_extract_pdf_text" in suggested
        assert "pdfbasic_analyze_pdf" in suggested
        assert "code_executor_run_python" not in suggested
    
    def test_csv_suggests_data_tools(self):
        files = {"data.csv": {"size": 500}}
        available_tools = [
            "data_analyzer_process_csv",
            "spreadsheet_read_table",
            "pdfbasic_extract_pdf_text",
        ]
        
        suggested = get_suggested_tools_for_files(files, available_tools)
        
        assert "data_analyzer_process_csv" in suggested
        assert "spreadsheet_read_table" in suggested
        assert "pdfbasic_extract_pdf_text" not in suggested
    
    def test_image_suggests_vision_tools(self):
        files = {"photo.jpg": {"size": 2000}}
        available_tools = [
            "vision_analyze_image",
            "ocr_extract_text",
            "pdfbasic_analyze_pdf",
        ]
        
        suggested = get_suggested_tools_for_files(files, available_tools)
        
        assert "vision_analyze_image" in suggested
        assert "ocr_extract_text" in suggested
    
    def test_multiple_files_different_types(self):
        files = {
            "report.pdf": {"size": 1000},
            "data.csv": {"size": 500},
        }
        available_tools = [
            "pdfbasic_extract_pdf_text",
            "csv_analyzer_process",
        ]
        
        suggested = get_suggested_tools_for_files(files, available_tools)
        
        assert "pdfbasic_extract_pdf_text" in suggested
        assert "csv_analyzer_process" in suggested
    
    def test_unknown_extension_suggests_nothing(self):
        files = {"unknown.xyz": {"size": 100}}
        available_tools = ["tool_a", "tool_b"]
        
        suggested = get_suggested_tools_for_files(files, available_tools)
        
        assert len(suggested) == 0
    
    def test_empty_files(self):
        suggested = get_suggested_tools_for_files({}, ["tool_a"])
        assert len(suggested) == 0
    
    def test_empty_available_tools(self):
        suggested = get_suggested_tools_for_files({"doc.pdf": {}}, [])
        assert len(suggested) == 0
    
    def test_none_inputs(self):
        assert get_suggested_tools_for_files(None, ["tool"]) == set()
        assert get_suggested_tools_for_files({"file.pdf": {}}, None) == set()


class TestMergeToolSelections:
    """Tests for merge_tool_selections function."""
    
    def test_user_selected_with_suggestions(self):
        user_selected = ["tool_a", "tool_b"]
        auto_suggested = {"tool_b", "tool_c"}
        
        merged = merge_tool_selections(user_selected, auto_suggested)
        
        assert set(merged) == {"tool_a", "tool_b", "tool_c"}
    
    def test_no_user_selection_with_suggestions(self):
        merged = merge_tool_selections(None, {"tool_a", "tool_b"})
        
        assert set(merged) == {"tool_a", "tool_b"}
    
    def test_user_selection_no_suggestions(self):
        merged = merge_tool_selections(["tool_a"], set())
        
        assert merged == ["tool_a"]
    
    def test_no_selections_at_all(self):
        merged = merge_tool_selections(None, set())
        
        assert merged is None
    
    def test_empty_user_selection_treated_as_none(self):
        # Empty list should still be truthy in Python, so tools remain
        merged = merge_tool_selections([], {"suggested"})
        
        # Empty list is falsy, so suggestions should be used
        assert "suggested" in (merged or [])


class TestFileToolSuggester:
    """Tests for FileToolSuggester class."""
    
    def test_suggest_without_tool_manager(self):
        suggester = FileToolSuggester(tool_manager=None)
        
        result = suggester.suggest_tools(
            files={"doc.pdf": {}},
            user_selected_tools=["existing_tool"]
        )
        
        # Without tool manager, should return original selection
        assert result == ["existing_tool"]
    
    def test_suggest_with_mock_tool_manager(self):
        class MockToolManager:
            def get_available_tools(self):
                return ["pdfbasic_extract_pdf_text", "other_tool"]
        
        suggester = FileToolSuggester(tool_manager=MockToolManager())
        
        result = suggester.suggest_tools(
            files={"document.pdf": {"size": 1000}},
            user_selected_tools=None
        )
        
        assert "pdfbasic_extract_pdf_text" in result
    
    def test_suggest_adds_to_user_selection(self):
        class MockToolManager:
            def get_available_tools(self):
                return ["pdfbasic_analyze_pdf", "code_run"]
        
        suggester = FileToolSuggester(tool_manager=MockToolManager())
        
        result = suggester.suggest_tools(
            files={"report.pdf": {}},
            user_selected_tools=["code_run"]
        )
        
        assert "code_run" in result
        assert "pdfbasic_analyze_pdf" in result
    
    def test_suggest_handles_tool_manager_error(self):
        class BrokenToolManager:
            def get_available_tools(self):
                raise RuntimeError("Connection failed")
        
        suggester = FileToolSuggester(tool_manager=BrokenToolManager())
        
        # Should not raise, returns original selection
        result = suggester.suggest_tools(
            files={"doc.pdf": {}},
            user_selected_tools=["existing"]
        )
        
        assert result == ["existing"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
