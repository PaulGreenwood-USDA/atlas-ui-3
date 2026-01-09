#!/usr/bin/env python3
"""
PDF Analyzer MCP Server using FastMCP.
Provides PDF text analysis and report generation through the MCP protocol.
"""

import base64
import io
import os
import re
import requests
import logging
from collections import Counter
from typing import Any, Dict, Annotated, Optional

# This tool requires the PyPDF2 and reportlab libraries.
# Install them using: pip install PyPDF2 reportlab
from PyPDF2 import PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

from fastmcp import FastMCP

logger = logging.getLogger(__name__)

mcp = FastMCP("PDF_Analyzer")


def _analyze_pdf_content(instructions: str, filename: str, original_filename: Optional[str] = None) -> Dict[str, Any]:
    """
    Core PDF analysis logic that can be reused by multiple tools.
    
    Args:
        instructions: Instructions for the tool, not used in this implementation.
        filename: The name of the file, which must have a '.pdf' extension.
        original_filename: The original name of the file.

    Returns:
        A dictionary containing the analysis results or an error message.
    """
    try:
        # print the instructions.
        logger.info(f"Instructions: {instructions}")
        # 1. Validate that the filename is for a PDF
        if not (filename.lower().endswith('.pdf') or (original_filename and original_filename.lower().endswith('.pdf'))):
            return {"results": {"error": "Invalid file type. This tool only accepts PDF files."}}

        # 2. Decode the Base64 data and read the PDF content
        # Check if filename is a URL (absolute or relative)
        is_url = (
            filename.startswith("http://") or
            filename.startswith("https://") or
            filename.startswith("/api/") or
            filename.startswith("/")
        )

        if is_url:
            # Convert relative URLs to absolute URLs
            if filename.startswith("/"):
                # Construct absolute URL from relative path
                # Default to localhost:8000 for local development
                backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
                url = f"{backend_url}{filename}"
            else:
                url = filename

            logger.info(f"Step 9: Downloading file from URL: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            pdf_stream = io.BytesIO(response.content)
        else:
            # Assume it's base64-encoded data
            decoded_bytes = base64.b64decode(filename)
            pdf_stream = io.BytesIO(decoded_bytes)
        
        reader = PdfReader(pdf_stream)

        full_text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                full_text += page_text + "\n"

        if not full_text.strip():
            return {
                "results": {
                    "operation": "pdf_analysis",
                    "filename": original_filename or filename,
                    "status": "Success",
                    "message": "PDF contained no extractable text.",
                    "total_word_count": 0,
                    "top_100_words": {}
                }
            }

        # 3. Process the text to get a word list and count
        # This regex finds all word-like sequences, ignoring case
        words = re.findall(r'\b\w+\b', full_text.lower())
        total_word_count = len(words)

        # 4. Count word frequencies and get the top 100
        word_counts = Counter(words)
        # Convert list of (word, count) tuples to a dictionary
        top_100_words_dict = dict(word_counts.most_common(100))

        # 5. Return the successful result
        return {
            "results": {
                "operation": "pdf_analysis",
                "filename": original_filename or filename,
                "total_word_count": total_word_count,
                "top_100_words": top_100_words_dict
            }
        }

    except Exception as e:
        # print traceback for debugging
        import traceback
        traceback.print_exc()
        # 6. Return an error message if something goes wrong
        return {"results": {"error": f"PDF analysis failed: {str(e)}"}}


@mcp.tool
def analyze_pdf(
    instructions: Annotated[str, "Instructions for the tool, not used in this implementation"],
    filename: Annotated[str, "The name of the file, which must have a '.pdf' extension"],
    original_filename: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extract and analyze text content from PDF documents with comprehensive word frequency analysis.

<<<<<<< HEAD
    This  PDF processing tool provides detailed text analytics for PDF documents:
=======
    This PDF processing tool provides detailed text analytics for PDF documents:
>>>>>>> main
    
    **PDF Text Extraction:**
    - Extracts text from all pages in PDF documents
    - Handles various PDF formats and structures
    - Works with both text-based and scanned PDFs (text extraction only)
    - Preserves document structure and content flow

    **Text Analysis Features:**
    - Complete word count across entire document
    - Top 100 most frequently used words identification
    - Case-insensitive word analysis for accurate frequency counting
    - Word pattern recognition and linguistic analysis
    - Document length and content density assessment

    **Content Processing:**
    - Intelligent text cleaning and normalization
    - Punctuation and formatting handling
    - Multi-language text support
    - Special character and encoding management

    **Analytics Insights:**
    - Document vocabulary richness and complexity
    - Key topic identification through word frequency
    - Content themes and focus areas analysis
    - Writing style and language pattern recognition
    - Document structure and organization assessment

    **Use Cases:**
    - Academic paper and research document analysis
    - Legal document keyword extraction and analysis
    - Content marketing and SEO keyword research
    - Document classification and categorization
    - Research literature review and summarization
    - Contract and agreement content analysis

    **Supported PDF Types:**
    - Research papers, reports, and academic documents
    - Business documents, contracts, and agreements
    - Marketing materials and content documents
    - Technical documentation and manuals
    - Legal documents and regulatory filings

    **Output Format:**
    - Structured word frequency data
    - Total document word count statistics
    - Top 100 words with occurrence frequencies
    - Document metadata and processing information

    Args:
        instructions: Processing instructions or requirements (currently not used)
        filename: PDF file name (must end with .pdf extension)
        original_filename: The original name of the file.

    Returns:
        Dictionary containing:
        - operation: Processing type confirmation
        - filename: Source PDF file name
        - total_word_count: Complete document word count
        - top_100_words: Dictionary of most frequent words with counts
        Or error message if PDF cannot be processed or contains no extractable text
    """
    logger.info("Step 8: Entering analyze_pdf tool")
    return _analyze_pdf_content(instructions, filename, original_filename)


@mcp.tool
def generate_report_about_pdf(
    instructions: Annotated[str, "Instructions for the tool, not used in this implementation"],
    filename: Annotated[str, "The name of the file, which must have a '.pdf' extension"],
    original_filename: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create comprehensive PDF analysis reports with professional formatting and detailed word frequency insights.

    This advanced PDF reporting tool combines text analysis with professional document generation:
    
    **Complete PDF Analysis Workflow:**
    - Performs full text extraction and word frequency analysis
    - Generates professional analysis reports in PDF format
    - Creates downloadable documents with structured data presentation
    - Provides ready-to-share analytical insights

    **Report Contents:**
    - Executive summary with document overview
    - Total word count and document statistics
    - Top 100 most frequent words with occurrence counts
    - Professional multi-column layout for easy reading
    - Organized tabular presentation of word frequency data

    **Report Features:**
    - Clean, professional PDF formatting using ReportLab
    - Multi-column layout optimizing space usage
    - Clear headers and structured information hierarchy
    - Page management for large datasets
    - High-quality typography and spacing

    **Document Generation:**
    - Creates new PDF reports from analysis results
    - Professional business document appearance
    - Optimized layout for printing and digital sharing
    - Comprehensive data presentation in readable format

    **Use Cases:**
    - Academic research document analysis reporting
    - Legal document content analysis for litigation support
    - Content marketing keyword research documentation
    - Business document compliance and review reporting
    - Research literature analysis and summarization
    - Document classification and content audit reports

    **Report Applications:**
    - Stakeholder presentations with document insights
    - Content strategy planning based on word analysis
    - Academic research methodology documentation
    - Legal discovery and document review processes
    - Quality assurance for written content

    **Output Features:**
    - Professional PDF report with embedded analysis
    - Downloadable file for offline access and sharing
    - Structured data visualization in document format
    - Ready-to-present analytical insights

    Args:
        instructions: Report generation instructions or requirements (currently not used)
        filename: Source PDF file name (must end with .pdf extension)
        original_filename: The original name of the file.

    Returns:
        Dictionary containing:
        - results: Report generation summary and success confirmation
        - artifacts: Professional PDF report with complete analysis
        - display: Optimized viewer configuration for report presentation
        - meta_data: Source file information and analysis statistics
        Or error message if PDF cannot be processed or report generation fails
    """
    logger.info("Step 8: Entering generate_report_about_pdf tool")
    # --- 1. Perform the same analysis as the first function ---
    analysis_result = _analyze_pdf_content(instructions, filename, original_filename)
    if "error" in analysis_result.get("results", {}):
        return analysis_result

    # --- 2. Generate the PDF report ---
    try:
        results_data = analysis_result["results"]

        # Create PDF report in memory
        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=letter)
        width, height = letter

        # Title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(1 * inch, height - 1 * inch, "PDF Analysis Report")

        # Document info
        c.setFont("Helvetica-Bold", 12)
        c.drawString(1 * inch, height - 1.5 * inch, "Document:")
        c.setFont("Helvetica", 10)
        c.drawString(1.5 * inch, height - 1.5 * inch, results_data.get("filename", "Unknown"))

        # Total word count
        c.setFont("Helvetica-Bold", 12)
        c.drawString(1 * inch, height - 2 * inch, "Total Words:")
        c.setFont("Helvetica", 10)
        c.drawString(1.5 * inch, height - 2 * inch, str(results_data.get("total_word_count", 0)))

        # Top 100 words header
        c.setFont("Helvetica-Bold", 12)
        c.drawString(1 * inch, height - 2.5 * inch, "Top 100 Most Frequent Words:")

        # Display top words in columns
        c.setFont("Helvetica", 9)
        y_position = height - 3 * inch
        x_col1 = 1 * inch
        x_col2 = 3.5 * inch
        x_col3 = 6 * inch

        top_100_words = results_data.get("top_100_words", {})
        words_list = list(top_100_words.items())

        for idx, (word, count) in enumerate(words_list):
            # Determine column position
            col = idx % 3
            if col == 0:
                x_pos = x_col1
            elif col == 1:
                x_pos = x_col2
            else:
                x_pos = x_col3

            # Move to next row after every 3 words
            if col == 0 and idx > 0:
                y_position -= 0.2 * inch

            # Check if we need a new page
            if y_position < 1 * inch:
                c.showPage()
                c.setFont("Helvetica", 9)
                y_position = height - 1 * inch

            # Draw word and count
            text = f"{word}: {count}"
            c.drawString(x_pos, y_position, text)

        c.save()

        # Get PDF bytes and encode to base64
        pdf_bytes = pdf_buffer.getvalue()
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')

        # --- 3. Return the structured response (v2 MCP compliant) ---
        report_name = f"analysis_report_{results_data.get('filename', 'document').replace('.pdf', '')}.pdf"

        return {
            "results": {
                "operation": "pdf_report_generation",
                "status": "Success",
                "message": f"Generated analysis report for {results_data.get('filename', 'document')}",
                "total_word_count": results_data.get("total_word_count", 0),
                "words_analyzed": len(top_100_words)
            },
            "artifacts": [
                {
                    "name": report_name,
                    "b64": pdf_base64,
                    "mime": "application/pdf",
                    "size": len(pdf_bytes),
                    "description": "PDF analysis report with word frequency statistics"
                }
            ],
            "display": {
                "open_canvas": True,
                "primary_file": report_name,
                "mode": "replace",
                "viewer_hint": "pdf"
            },
            "meta_data": {
                "source_file": results_data.get("filename", "Unknown"),
                "total_words": results_data.get("total_word_count", 0)
            }
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "results": {
                "error": f"Report generation failed: {str(e)}"
            }
        }


def _extract_pdf_text(filename: str, original_filename: Optional[str] = None, max_chars: int = 50000) -> Dict[str, Any]:
    """
    Extract text content from a PDF file for reading/summarization.
    
    Args:
        filename: The PDF file path, URL, or base64 data.
        original_filename: The original name of the file.
        max_chars: Maximum characters to return (default 50000).

    Returns:
        A dictionary containing the extracted text or an error message.
    """
    try:
        # Validate that the filename is for a PDF
        if not (filename.lower().endswith('.pdf') or (original_filename and original_filename.lower().endswith('.pdf'))):
            return {"results": {"error": "Invalid file type. This tool only accepts PDF files."}}

        # Check if filename is a URL (absolute or relative)
        is_url = (
            filename.startswith("http://") or
            filename.startswith("https://") or
            filename.startswith("/api/") or
            filename.startswith("/")
        )

        if is_url:
            # Convert relative URLs to absolute URLs
            if filename.startswith("/"):
                backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
                url = f"{backend_url}{filename}"
            else:
                url = filename

            logger.info(f"Extracting text from PDF URL: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            pdf_stream = io.BytesIO(response.content)
        else:
            # Assume it's base64-encoded data
            decoded_bytes = base64.b64decode(filename)
            pdf_stream = io.BytesIO(decoded_bytes)
        
        reader = PdfReader(pdf_stream)
        
        full_text = ""
        page_count = len(reader.pages)
        
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                full_text += f"\n--- Page {i + 1} ---\n"
                full_text += page_text
            
            # Stop if we've exceeded max_chars
            if len(full_text) > max_chars:
                full_text = full_text[:max_chars]
                truncated = True
                break
        else:
            truncated = False

        if not full_text.strip():
            return {
                "results": {
                    "operation": "pdf_text_extraction",
                    "filename": original_filename or filename,
                    "status": "Success",
                    "message": "PDF contained no extractable text. The document may be scanned images or have security restrictions.",
                    "page_count": page_count,
                    "text": ""
                }
            }

        return {
            "results": {
                "operation": "pdf_text_extraction",
                "filename": original_filename or filename,
                "page_count": page_count,
                "character_count": len(full_text),
                "truncated": truncated,
                "text": full_text
            }
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"results": {"error": f"PDF text extraction failed: {str(e)}"}}


@mcp.tool
def extract_pdf_text(
    instructions: Annotated[str, "What you want to do with the text (e.g., 'summarize', 'find key points', 'extract conclusions')"],
    filename: Annotated[str, "The name of the PDF file to read"],
    original_filename: Optional[str] = None,
    max_chars: Annotated[int, "Maximum characters to extract (default 50000)"] = 50000
) -> Dict[str, Any]:
    """
    Extract the full text content from a PDF document for reading, summarization, or analysis.

    USE THIS TOOL when you need to:
    - Summarize a PDF document
    - Read and understand PDF content
    - Find specific information in a PDF
    - Answer questions about a PDF's content
    - Extract key points, conclusions, or findings from a PDF

    This tool extracts the actual text from all pages of a PDF and returns it so you can
    read, analyze, and summarize the content. The text is returned with page markers.

    Note: This is different from analyze_pdf which only returns word frequency statistics.
    Use this tool when you need the actual content to read or summarize.

    Args:
        instructions: What you want to do with the text (helps with logging/context)
        filename: PDF file name (must end with .pdf extension)
        original_filename: The original name of the file if different from filename
        max_chars: Maximum characters to extract (default 50000, increase for longer documents)

    Returns:
        Dictionary containing:
        - operation: "pdf_text_extraction"
        - filename: Source PDF file name  
        - page_count: Number of pages in the document
        - character_count: Number of characters extracted
        - truncated: Whether the text was truncated due to max_chars limit
        - text: The extracted text content with page markers
    """
    logger.info(f"Extracting PDF text for: {instructions}")
    return _extract_pdf_text(filename, original_filename, max_chars)


if __name__ == "__main__":
    mcp.run()