# CLAUDE.md

Project context for AI assistants working on `claude-json-to-markdown`.

## Quick Reference

```bash
uv run pytest          # Run all tests
uv run pytest -x       # Stop on first failure
uv run cj2md --help    # CLI usage
```

## Architecture

```
src/claude_json2md/
├── cli.py           # Typer CLI, argument parsing, RenderOptions assembly
├── converter.py     # Core logic: JSON parsing, conversation iteration, file writing
├── renderers.py     # Content rendering: thinking blocks, tools, citations, artifacts
├── log_setup.py     # Logging config via platformdirs + logging_config.json
└── logging_config.json
```

**Data flow**: `cli.py` → `converter.py` (orchestration) → `renderers.py` (formatting)

## Key Patterns

- **RenderOptions dataclass**: Passed through to control what content types appear in output
- **Opt-out flags**: New content types default ON, users disable with `--no-*` flags
- **Tool operations as-is**: Artifacts show create/update/rewrite operations, not reconstructed content
- **Graceful degradation**: Missing/empty fields handled silently, not errors

## Testing

- `tests/test_converter_units.py` - Unit tests for converter functions
- `tests/test_converter_integration.py` - End-to-end CLI tests with temp files
- `tests/test_renderers.py` - Renderer output formatting tests

## Input Format

The tool processes Anthropic's conversation export JSON. Key structures:

```python
conversation["chat_messages"][n]["content"]  # List of content blocks
content_block["type"]  # "text", "tool_use", "tool_result", "thinking"
content_block["thinking"]  # For thinking blocks
content_block["name"]  # Tool name for tool_use blocks
```

## When Adding Features

1. Add CLI flag to `cli.py` (follow `--no-*` pattern for opt-out)
2. Add field to `RenderOptions` dataclass in `renderers.py`
3. Implement rendering logic in `renderers.py`
4. Wire up in `converter.py` if needed
5. Add tests for new functionality
