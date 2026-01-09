# Changelog

All notable changes to Atlas UI 3 will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### 2026-01-09 - Critical Security Hardening
- **Security**: Remove exposed API key from `.env` file (CEREBRAS_API_KEY) - never commit real keys to version control
- **Security**: Add explicit JWT algorithm whitelist (ES256, RS256) to prevent algorithm substitution attacks in AWS ALB JWT verification
- **Security**: Strengthen capability token validation - now fails hard in production if CAPABILITY_TOKEN_SECRET is not configured
- **Security**: Add comprehensive file upload validation including size limits (configurable via FILE_UPLOAD_MAX_SIZE_MB), extension allowlisting, path traversal protection, and null byte checks
- **Security**: Add Permissions-Policy security header to restrict browser features (geolocation, microphone, camera, payment, usb)
- **Security**: Improve authentication failure logging - distinguish expected failures (warning level) from unexpected errors (error level) for better security monitoring
- **Security**: Replace bare except clause in csv_reporter with specific exception handling (ValueError, TypeError)
- **Security**: Update `.env.example` with comprehensive security documentation and production warnings
- **Config**: Add file_upload_max_size_mb and file_upload_allowed_extensions settings to AppSettings
- **Config**: Add security_permissions_policy_enabled and security_permissions_policy_value settings for Permissions-Policy header
- **Fix**: Agent loop now handles models that don't properly set `finish: true` flag (e.g., Cerebras). Added fallback detection for `final_answer` without finish flag, and consecutive-think limit to prevent infinite loops.
- **Feature**: Add `extract_pdf_text` tool to pdfbasic MCP server for actual PDF text extraction and summarization. The existing `analyze_pdf` tool only returns word frequency statistics; this new tool returns the actual text content so the LLM can summarize documents.
- **Feature**: Add tool call content parser (`backend/modules/llm/tool_call_parser.py`) for models that don't support native function calling. When a model outputs tool calls as JSON in its text content (e.g., Cerebras outputs `{"cmd": [...]}` as text), the parser extracts and converts them to the proper tool_calls format. Supports multiple JSON formats (OpenAI-style, function/args, tool/parameters, and direct tool-name-as-key patterns).
- **Feature**: Add automatic tool suggestion based on file attachments (`backend/application/chat/preprocessors/file_tool_suggester.py`). When users attach files (PDF, CSV, images, etc.), relevant tools are automatically selected. For example, attaching a PDF auto-selects `pdfbasic_extract_pdf_text` so the model can read and summarize the document without manual tool selection.

### 2026-01-07 - Elicitation Routing Fix and Testing
- **Fix**: Resolve elicitation dialog not appearing by switching from `contextvars.ContextVar` to dictionary-based routing. The MCP receive loop runs in a separate asyncio task that cannot access context variables set in the tool execution task. Now uses per-server routing with proper cross-task visibility.
- **Fix**: Add `setPendingElicitation` to WebSocket handler destructuring so dialog state updates work correctly.
- **Fix**: Add `sendMessage` to ChatContext exports so ElicitationDialog can send responses.
- **Fix**: Close elicitation dialog after user responds (accept/decline/cancel).
- Add comprehensive logging to trace `update_callback` flow from WebSocket to MCP tool execution.
- Add validation and fallback mechanism in `ToolsModeRunner` to ensure update_callback is never None during tool execution.
- Create per-server elicitation handlers using closures to capture server_name for proper routing.
- **Tests**: Add comprehensive unit tests for elicitation routing (8 backend tests, 7 frontend tests) to prevent regression.

### PR #191 - 2026-01-06
- **MCP Tool Elicitation Support**: Implemented full support for MCP tool elicitation (FastMCP 2.10.0+), allowing tools to request structured user input during execution via `ctx.elicit()`. Includes backend elicitation manager, WebSocket message handling, and a modal dialog UI supporting string, number, boolean, enum, and structured multi-field forms.
- **Elicitation Demo Server**: Added `elicitation_demo` MCP server showcasing all elicitation types including scalar inputs, enum selections, structured forms, multi-turn flows, and approval-only requests.
- Fix elicitation handler integration to use `client.set_elicitation_callback()` instead of passing as kwarg (resolves FastMCP API compatibility).
- Admin UI: Fix duplicate "MCP Configuration & Controls" card rendering.
- Admin UI: Clarify MCP Server Manager note that available configs are loaded from `config/mcp-example-configs/`.

### PR #190 - 2026-01-05
- Add a "Back to Admin Dashboard" navigation button to the admin LogViewer.

### PR #184 - 2025-12-19
- Add configurable log levels for controlling sensitive data logging. Set `LOG_LEVEL=INFO` in production to prevent logging user input/output content, or `LOG_LEVEL=DEBUG` for development/testing with verbose logging.
- Fix logging in error_utils.py to prevent full LLM response objects from being logged at INFO level.
- Redact tool approval response logging so tool arguments are never logged at INFO.
- Remove unused local variables in test_log_level_sensitive_data.py (code quality improvement).

### PR #180 - 2025-12-17
- Add MCP Server Management admin panel and update Admin Dashboard panel layout.

### PR #181 - 2025-12-17
- Add unsaved changes confirmation dialog to tools panel

### PR 177 Security Fixes - 2025-12-13
- **SECURITY FIX**: Fixed MD5 hash usage in S3 client by adding `usedforsecurity=False` parameter to address cryptographic security warnings while maintaining S3 ETag compatibility
- **SECURITY FIX**: Enhanced network binding security by making host binding configurable via `ATLAS_HOST` environment variable, defaulting to localhost (127.0.0.1) for secure development while allowing 0.0.0.0 for production deployments
- Updated Docker configuration to properly handle new host binding environment variable
### PR #176 - 2025-12-15
- Add Quay.io container registry CI/CD workflow for automated container publishing from main and develop branches
- Update README and Getting Started guide with Quay.io pre-built image information

### PR #173 - 2025-12-13
- Increase unit test coverage across backend and frontend; add useSettings localStorage error-handling tests and harden the hook against localStorage failures.
### PR #169 - 2025-12-11
- Implement MCP server logging infrastructure with FastMCP log_handler
- Add log level filtering based on environment LOG_LEVEL configuration
- Forward MCP server logs to chat UI via intermediate_update websocket messages
- Add visual indicators (badges and colors) for different log levels (debug, info, warning, error, alert)
- Create comprehensive test suite for MCP logging functionality
- Add demo MCP server (logging_demo) for testing log output

### PR #172 - 2025-12-13
- Resolve all frontend ESLint errors and warnings; update ESLint config and tests for consistency.
### PR #170 - 2025-12-12
- Improve LogViewer performance by memoizing expensive computations with `useMemo`


### PR  163 - 2024-12-09
- **SECURITY FIX**: Fixed edit args security bug that allowed bypassing username override security through approval argument editing
- Added username-override-demo MCP server to demonstrate the username security feature
- Server includes tools showing how Atlas UI prevents LLM user impersonation
- Added comprehensive documentation and example configuration

### PR #158 - 2025-12-10
- Add explicit "Save Changes" and "Cancel" buttons to Tools & Integration Panel (ToolsPanel)
- Add explicit "Save Changes" and "Cancel" buttons to Data Sources Panel (RagPanel)
- Implement pending state pattern to track unsaved changes
- Save button is disabled when no changes are made, enabled when changes are pending
- Changes only persist to localStorage when user clicks "Save Changes"
- Cancel button reverts all pending changes and closes panel
- Updated tests to verify save/cancel functionality


### PR #156 - 2024-12-07
- Add CHANGELOG.md to track changes across PRs
- Update agent instructions to require changelog entries for each PR

## Recent Changes

### PR #157 - 2024-12-07
- Enhanced ToolsPanel UI with improved visual separation between tools and prompts
- Added section headers with icons for tools and prompts
- Updated color scheme to use consistent green styling for both tools and prompts
- Added horizontal divider between tools and prompts sections
- Increased font size and weight for section headers
- Improved vertical spacing between UI sections

### PR #155 - 2024-12-06
- Add automated documentation bundling for CI/CD artifacts
