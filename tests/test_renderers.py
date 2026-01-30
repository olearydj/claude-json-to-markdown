"""Tests for the renderers module."""

from claude_json2md.renderers import (
    RenderOptions,
    CitationCollector,
    render_text,
    render_thinking,
    render_voice_note,
    render_tool_use,
    render_tool_result,
    render_content_item,
)


class TestCitationCollector:
    def test_add_returns_sequential_numbers(self):
        collector = CitationCollector()
        assert collector.add("https://a.com") == 1
        assert collector.add("https://b.com") == 2
        assert collector.add("https://c.com") == 3

    def test_add_deduplicates_urls(self):
        collector = CitationCollector()
        assert collector.add("https://a.com") == 1
        assert collector.add("https://b.com") == 2
        assert collector.add("https://a.com") == 1  # Same as first

    def test_render_references_section_empty(self):
        collector = CitationCollector()
        refs = collector.render_references_section()
        assert refs == []

    def test_render_references_section_with_citations(self):
        collector = CitationCollector()
        collector.add("https://example.com")
        collector.add("https://python.org")
        refs = collector.render_references_section()
        assert "## References" in refs
        assert "1. https://example.com" in refs
        assert "2. https://python.org" in refs


class TestRenderText:
    def test_renders_text(self):
        item = {"type": "text", "text": "Hello world"}
        options = RenderOptions()
        lines = render_text(item, options, CitationCollector())
        assert "Hello world" in lines

    def test_empty_text_returns_empty(self):
        item = {"type": "text", "text": ""}
        options = RenderOptions()
        lines = render_text(item, options, CitationCollector())
        assert lines == []

    def test_collects_citations(self):
        item = {
            "type": "text",
            "text": "See reference",
            "citations": [{"url": "https://example.com"}],
        }
        options = RenderOptions()
        citations = CitationCollector()
        render_text(item, options, citations)
        refs = citations.render_references_section()
        refs_text = "\n".join(refs)
        assert "https://example.com" in refs_text

    def test_collects_nested_citations(self):
        """Citations can have url in details.url format."""
        item = {
            "type": "text",
            "text": "See reference",
            "citations": [{"details": {"url": "https://nested.com"}}],
        }
        options = RenderOptions()
        citations = CitationCollector()
        render_text(item, options, citations)
        refs = citations.render_references_section()
        refs_text = "\n".join(refs)
        assert "https://nested.com" in refs_text


class TestRenderThinking:
    def test_renders_collapsible(self):
        item = {"type": "thinking", "thinking": "Deep thought"}
        options = RenderOptions()
        lines = render_thinking(item, options, CitationCollector())
        assert "<details>" in lines
        assert "<summary>Thinking</summary>" in lines
        assert "Deep thought" in lines
        assert "</details>" in lines

    def test_respects_option_disabled(self):
        item = {"type": "thinking", "thinking": "Deep thought"}
        options = RenderOptions(include_thinking=False)
        lines = render_thinking(item, options, CitationCollector())
        assert lines == []

    def test_empty_thinking_returns_empty(self):
        item = {"type": "thinking", "thinking": ""}
        options = RenderOptions()
        lines = render_thinking(item, options, CitationCollector())
        assert lines == []


class TestRenderVoiceNote:
    def test_renders_voice_note(self):
        item = {
            "type": "voice_note",
            "title": "Quick question",
            "text": "What is life?",
        }
        options = RenderOptions()
        lines = render_voice_note(item, options, CitationCollector())
        assert "**[Voice Note: Quick question]**" in lines
        assert "What is life?" in lines

    def test_default_title(self):
        item = {"type": "voice_note", "text": "Hello there"}
        options = RenderOptions()
        lines = render_voice_note(item, options, CitationCollector())
        assert "**[Voice Note: Voice Note]**" in lines

    def test_empty_text_returns_empty(self):
        item = {"type": "voice_note", "title": "Empty", "text": ""}
        options = RenderOptions()
        lines = render_voice_note(item, options, CitationCollector())
        assert lines == []


class TestRenderToolUse:
    def test_web_search(self):
        item = {
            "type": "tool_use",
            "name": "web_search",
            "input": {"query": "python tutorials"},
        }
        options = RenderOptions()
        lines = render_tool_use(item, options, CitationCollector())
        text = "\n".join(lines)
        assert "**Tool: web_search**" in text
        assert "Query: `python tutorials`" in text

    def test_artifacts_create(self):
        item = {
            "type": "tool_use",
            "name": "artifacts",
            "input": {
                "command": "create",
                "id": "my-artifact",
                "title": "My Document",
                "type": "text/markdown",
                "language": "markdown",
            },
        }
        options = RenderOptions()
        lines = render_tool_use(item, options, CitationCollector())
        text = "\n".join(lines)
        assert "**Tool: artifacts**" in text
        assert "Command: `create`" in text
        assert "ID: `my-artifact`" in text
        assert "Title: My Document" in text
        assert "Type: text/markdown" in text

    def test_artifacts_update(self):
        item = {
            "type": "tool_use",
            "name": "artifacts",
            "input": {
                "command": "update",
                "id": "my-artifact",
                "old_str": "old text",
                "new_str": "new text",
            },
        }
        options = RenderOptions()
        lines = render_tool_use(item, options, CitationCollector())
        text = "\n".join(lines)
        assert "Command: `update`" in text
        assert "ID: `my-artifact`" in text

    def test_create_file(self):
        item = {
            "type": "tool_use",
            "name": "create_file",
            "input": {
                "path": "/home/user/doc.md",
                "description": "A markdown document",
            },
        }
        options = RenderOptions()
        lines = render_tool_use(item, options, CitationCollector())
        text = "\n".join(lines)
        assert "**Tool: create_file**" in text
        assert "Path: `/home/user/doc.md`" in text
        assert "Description: A markdown document" in text

    def test_respects_no_tools_option(self):
        item = {"type": "tool_use", "name": "web_search", "input": {"query": "test"}}
        options = RenderOptions(include_tools=False)
        lines = render_tool_use(item, options, CitationCollector())
        assert lines == []

    def test_verbose_shows_content(self):
        item = {
            "type": "tool_use",
            "name": "artifacts",
            "input": {
                "command": "create",
                "id": "code",
                "content": "print('hello')",
                "language": "python",
            },
        }
        options = RenderOptions(verbose_tools=True)
        lines = render_tool_use(item, options, CitationCollector())
        assert "```python" in lines
        assert "print('hello')" in lines


class TestRenderToolResult:
    def test_renders_result(self):
        item = {"type": "tool_result", "name": "web_search", "is_error": False}
        options = RenderOptions()
        lines = render_tool_result(item, options, CitationCollector())
        assert "**Tool Result: web_search**" in lines

    def test_renders_error(self):
        item = {
            "type": "tool_result",
            "name": "web_search",
            "is_error": True,
            "content": "Connection timeout",
        }
        options = RenderOptions()
        lines = render_tool_result(item, options, CitationCollector())
        assert "**Tool Error: web_search**" in lines
        assert "Connection timeout" in lines

    def test_respects_no_tools_option(self):
        item = {"type": "tool_result", "name": "test", "is_error": False}
        options = RenderOptions(include_tools=False)
        lines = render_tool_result(item, options, CitationCollector())
        assert lines == []


class TestRenderContentItem:
    def test_dispatches_to_text(self):
        item = {"type": "text", "text": "Hello"}
        options = RenderOptions()
        lines = render_content_item(item, options, CitationCollector())
        assert "Hello" in lines

    def test_dispatches_to_thinking(self):
        item = {"type": "thinking", "thinking": "Hmm..."}
        options = RenderOptions()
        lines = render_content_item(item, options, CitationCollector())
        assert "<details>" in lines
        assert "Hmm..." in lines

    def test_unknown_type_falls_back_to_text(self):
        item = {"type": "unknown_type", "text": "Fallback content"}
        options = RenderOptions()
        lines = render_content_item(item, options, CitationCollector())
        assert "Fallback content" in lines

    def test_missing_type_defaults_to_text(self):
        item = {"text": "No type field"}
        options = RenderOptions()
        lines = render_content_item(item, options, CitationCollector())
        assert "No type field" in lines
