"""
File-based tool suggestion service.

Automatically suggests relevant tools based on attached file types.
For example, suggests PDF tools when a PDF is attached.
"""

import logging
from typing import Dict, Any, List, Optional, Set

logger = logging.getLogger(__name__)

# Mapping of file extensions to relevant tool name patterns
# The patterns are matched against available tool names (case-insensitive)
FILE_TYPE_TOOL_PATTERNS: Dict[str, List[str]] = {
    # PDF files
    ".pdf": ["pdf", "document", "extract_text"],
    
    # Image files
    ".png": ["image", "vision", "ocr"],
    ".jpg": ["image", "vision", "ocr"],
    ".jpeg": ["image", "vision", "ocr"],
    ".gif": ["image", "vision"],
    ".webp": ["image", "vision"],
    ".bmp": ["image", "vision", "ocr"],
    
    # Document files
    ".doc": ["document", "word", "extract_text"],
    ".docx": ["document", "word", "extract_text"],
    ".txt": ["text", "document"],
    ".md": ["markdown", "text", "document"],
    ".rtf": ["document", "text"],
    
    # Spreadsheet files
    ".csv": ["csv", "spreadsheet", "data", "table"],
    ".xlsx": ["excel", "spreadsheet", "data", "table"],
    ".xls": ["excel", "spreadsheet", "data", "table"],
    
    # Code files
    ".py": ["python", "code", "execute"],
    ".js": ["javascript", "code"],
    ".ts": ["typescript", "code"],
    ".json": ["json", "data"],
    ".yaml": ["yaml", "data"],
    ".yml": ["yaml", "data"],
    
    # Data files
    ".xml": ["xml", "data"],
    ".html": ["html", "web", "scrape"],
    
    # Archive files
    ".zip": ["archive", "extract"],
    ".tar": ["archive", "extract"],
    ".gz": ["archive", "extract"],
}


def get_file_extension(filename: str) -> str:
    """Extract lowercase file extension from filename."""
    if "." in filename:
        return "." + filename.rsplit(".", 1)[-1].lower()
    return ""


def get_suggested_tools_for_files(
    files: Optional[Dict[str, Any]],
    available_tools: List[str]
) -> Set[str]:
    """
    Suggest relevant tools based on attached files.
    
    Args:
        files: Dictionary of attached files (filename -> file info)
        available_tools: List of available tool names
        
    Returns:
        Set of suggested tool names
    """
    if not files or not available_tools:
        return set()
    
    suggested = set()
    available_lower = {tool.lower(): tool for tool in available_tools}
    
    for filename in files.keys():
        ext = get_file_extension(filename)
        if ext not in FILE_TYPE_TOOL_PATTERNS:
            continue
            
        patterns = FILE_TYPE_TOOL_PATTERNS[ext]
        
        # Find tools that match any pattern for this file type
        for tool_lower, tool_original in available_lower.items():
            for pattern in patterns:
                if pattern in tool_lower:
                    suggested.add(tool_original)
                    logger.debug(f"Suggested tool '{tool_original}' for file '{filename}' (pattern: {pattern})")
                    break
    
    return suggested


def merge_tool_selections(
    user_selected: Optional[List[str]],
    auto_suggested: Set[str]
) -> Optional[List[str]]:
    """
    Merge user-selected tools with auto-suggested tools.
    
    If user has selected tools, adds suggestions to their selection.
    If user has not selected any tools but we have suggestions, use those.
    If neither, return None (plain mode).
    
    Args:
        user_selected: Tools explicitly selected by user
        auto_suggested: Tools auto-suggested based on files
        
    Returns:
        Merged list of tools, or None if no tools
    """
    if user_selected:
        # User has selections - add any suggestions not already included
        merged = set(user_selected)
        new_suggestions = auto_suggested - merged
        if new_suggestions:
            logger.info(f"Auto-adding suggested tools based on attached files: {new_suggestions}")
            merged.update(new_suggestions)
        return list(merged)
    
    if auto_suggested:
        # No user selection but we have suggestions
        logger.info(f"Auto-selecting tools based on attached files: {auto_suggested}")
        return list(auto_suggested)
    
    # No tools at all
    return None


class FileToolSuggester:
    """
    Service for suggesting tools based on attached files.
    
    Analyzes attached files and suggests relevant tools that can
    process those file types.
    """
    
    def __init__(self, tool_manager=None):
        """
        Initialize the suggester.
        
        Args:
            tool_manager: Optional tool manager to get available tools
        """
        self.tool_manager = tool_manager
    
    def suggest_tools(
        self,
        files: Optional[Dict[str, Any]],
        user_selected_tools: Optional[List[str]] = None
    ) -> Optional[List[str]]:
        """
        Suggest tools based on attached files.
        
        Args:
            files: Dictionary of attached files
            user_selected_tools: Tools already selected by user
            
        Returns:
            Updated tool selection including suggestions, or None
        """
        if not self.tool_manager:
            return user_selected_tools
        
        try:
            available_tools = self.tool_manager.get_available_tools()
            suggested = get_suggested_tools_for_files(files, available_tools)
            return merge_tool_selections(user_selected_tools, suggested)
        except Exception as e:
            logger.warning(f"Error suggesting tools for files: {e}")
            return user_selected_tools
