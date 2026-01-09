# Testing Guide

Comprehensive guide for testing Atlas UI 3 components.

## Test Structure

```
test/
├── run_tests.sh          # Main test runner
├── backend_tests.sh      # Backend test script
├── frontend_tests.sh     # Frontend test script
├── e2e_tests.sh          # E2E test script
└── README.md

backend/tests/
├── test_*.py             # Unit tests
└── integration/          # Integration tests

frontend/
├── src/**/*.test.js      # Component tests
└── e2e/                  # Playwright E2E tests
```

## Running Tests

### All Tests

```bash
./test/run_tests.sh all
```

### Backend Tests

```bash
./test/run_tests.sh backend

# Or directly with pytest
cd backend
../.venv/Scripts/python -m pytest tests/ -v
```

### Frontend Tests

```bash
./test/run_tests.sh frontend

# Or directly with vitest
cd frontend
npm test
```

### E2E Tests

```bash
./test/run_tests.sh e2e

# Or directly with Playwright
cd frontend
npx playwright test
```

## Backend Testing

### Unit Tests

Located in `backend/tests/`:

```python
# backend/tests/test_example.py
import pytest
from application.chat.preprocessors.file_tool_suggester import (
    get_file_extension,
    get_suggested_tools_for_files,
)


class TestGetFileExtension:
    def test_pdf_extension(self):
        assert get_file_extension("document.pdf") == ".pdf"
    
    def test_no_extension(self):
        assert get_file_extension("filename") == ""


class TestGetSuggestedToolsForFiles:
    def test_pdf_suggests_pdf_tools(self):
        files = {"document.pdf": {"size": 1000}}
        available_tools = ["pdfbasic_extract_pdf_text", "other_tool"]
        
        suggested = get_suggested_tools_for_files(files, available_tools)
        
        assert "pdfbasic_extract_pdf_text" in suggested
```

### Async Tests

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result == expected
```

### Mocking

```python
from unittest.mock import patch, MagicMock, AsyncMock

@patch('modules.llm.litellm_caller.acompletion')
async def test_llm_call(mock_acompletion):
    mock_acompletion.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="response"))]
    )
    
    result = await llm_caller.call_plain("model", messages)
    
    assert result == "response"
    mock_acompletion.assert_called_once()
```

### Fixtures

```python
# backend/tests/conftest.py
import pytest

@pytest.fixture
def mock_tool_manager():
    manager = MagicMock()
    manager.get_available_tools.return_value = ["tool_a", "tool_b"]
    return manager

@pytest.fixture
def sample_messages():
    return [
        {"role": "system", "content": "You are helpful"},
        {"role": "user", "content": "Hello"}
    ]
```

### Running Specific Tests

```bash
# Run a specific file
pytest tests/test_file_tool_suggester.py -v

# Run a specific class
pytest tests/test_file_tool_suggester.py::TestGetFileExtension -v

# Run a specific test
pytest tests/test_file_tool_suggester.py::TestGetFileExtension::test_pdf_extension -v

# Run tests matching a pattern
pytest -k "pdf" -v
```

## Frontend Testing

### Component Tests (Vitest)

```javascript
// frontend/src/components/Button.test.jsx
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import Button from './Button';

describe('Button', () => {
  it('renders with text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click</Button>);
    
    fireEvent.click(screen.getByText('Click'));
    
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

### Context Tests

```javascript
// frontend/src/contexts/ChatContext.test.jsx
import { renderHook, act } from '@testing-library/react';
import { ChatProvider, useChatContext } from './ChatContext';

describe('ChatContext', () => {
  it('adds messages', () => {
    const wrapper = ({ children }) => (
      <ChatProvider>{children}</ChatProvider>
    );
    
    const { result } = renderHook(() => useChatContext(), { wrapper });
    
    act(() => {
      result.current.addMessage({ role: 'user', content: 'Hello' });
    });
    
    expect(result.current.messages).toHaveLength(1);
  });
});
```

### Mocking WebSocket

```javascript
import { vi } from 'vitest';

const mockWebSocket = {
  send: vi.fn(),
  close: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
};

vi.mock('../contexts/WSContext', () => ({
  useWebSocket: () => ({
    sendMessage: mockWebSocket.send,
    isConnected: true,
  }),
}));
```

## E2E Testing (Playwright)

### Test Structure

```javascript
// frontend/e2e/chat.spec.js
import { test, expect } from '@playwright/test';

test.describe('Chat', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:8000');
  });

  test('sends a message', async ({ page }) => {
    // Type in input
    await page.fill('[data-testid="chat-input"]', 'Hello');
    
    // Click send
    await page.click('[data-testid="send-button"]');
    
    // Wait for response
    await expect(page.locator('.assistant-message')).toBeVisible();
  });
});
```

### Running E2E Tests

```bash
# Run all E2E tests
npx playwright test

# Run with UI
npx playwright test --ui

# Run specific test file
npx playwright test e2e/chat.spec.js

# Debug mode
npx playwright test --debug
```

### Playwright Configuration

```javascript
// frontend/playwright.config.js
export default {
  testDir: './e2e',
  timeout: 30000,
  use: {
    baseURL: 'http://localhost:8000',
    trace: 'on-first-retry',
  },
  webServer: {
    command: 'cd ../backend && python main.py',
    port: 8000,
    reuseExistingServer: true,
  },
};
```

## Test Coverage

### Backend Coverage

```bash
pytest --cov=backend --cov-report=html tests/
# View report at htmlcov/index.html
```

### Frontend Coverage

```bash
npm test -- --coverage
```

## Writing Good Tests

### 1. Test Behavior, Not Implementation

```python
# Good - tests behavior
def test_extracts_pdf_tools_for_pdf_files():
    result = suggest_tools({"doc.pdf": {}}, ["pdf_tool"])
    assert "pdf_tool" in result

# Bad - tests implementation
def test_calls_pattern_matcher():
    with patch('suggester._match_pattern') as mock:
        suggest_tools(...)
        mock.assert_called()
```

### 2. Use Descriptive Names

```python
# Good
def test_returns_empty_set_when_no_files_provided():
    ...

# Bad
def test_1():
    ...
```

### 3. One Assertion Per Test (When Practical)

```python
# Good - focused tests
def test_extracts_pdf_extension():
    assert get_extension("doc.pdf") == ".pdf"

def test_handles_uppercase_extension():
    assert get_extension("doc.PDF") == ".pdf"
```

### 4. Arrange-Act-Assert

```python
def test_merges_user_and_suggested_tools():
    # Arrange
    user_tools = ["tool_a"]
    suggested = {"tool_b"}
    
    # Act
    result = merge_selections(user_tools, suggested)
    
    # Assert
    assert set(result) == {"tool_a", "tool_b"}
```

## CI/CD Integration

Tests run automatically on PR:

```yaml
# .github/workflows/test.yml
- name: Run Tests
  run: ./test/run_tests.sh all
```

## Debugging Failed Tests

### Verbose Output

```bash
pytest -v --tb=long
```

### Print Statements

```python
def test_something():
    result = function()
    print(f"DEBUG: result = {result}")  # Shows in pytest output with -s
    assert result == expected
```

### Debugger

```python
def test_something():
    import pdb; pdb.set_trace()  # Drops into debugger
    result = function()
```

### Playwright Debug

```bash
npx playwright test --debug
```
