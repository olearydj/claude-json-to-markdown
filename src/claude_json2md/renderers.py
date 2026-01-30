"""Content type renderers for markdown output."""

from dataclasses import dataclass
from typing import Callable
import json


@dataclass
class RenderOptions:
    """Configuration for markdown rendering behavior."""

    include_summary: bool = True
    include_thinking: bool = True
    include_citations: bool = True
    include_tools: bool = True
    verbose_tools: bool = False


class CitationCollector:
    """Collects and deduplicates citations across a conversation."""

    def __init__(self):
        self._citations: dict[str, int] = {}  # url -> ref_number
        self._ordered: list[str] = []

    def add(self, url: str) -> int:
        """Add citation, return reference number (1-indexed)."""
        if url not in self._citations:
            self._ordered.append(url)
            self._citations[url] = len(self._ordered)
        return self._citations[url]

    def render_references_section(self) -> list[str]:
        """Render the References section at end of document."""
        if not self._ordered:
            return []
        lines = ["", "## References", ""]
        for i, url in enumerate(self._ordered, 1):
            lines.append(f"{i}. {url}")
        return lines


def render_text(
    item: dict, options: RenderOptions, citations: CitationCollector
) -> list[str]:
    """Render a text content item."""
    text = item.get("text", "").strip()
    if not text:
        return []

    lines = [text, ""]

    # Collect citations if present
    if options.include_citations:
        item_citations = item.get("citations", [])
        for cit in item_citations:
            if isinstance(cit, dict):
                url = cit.get("url") or cit.get("details", {}).get("url")
                if url:
                    citations.add(url)

    return lines


def render_thinking(
    item: dict, options: RenderOptions, citations: CitationCollector
) -> list[str]:
    """Render a thinking content item as a collapsible block."""
    if not options.include_thinking:
        return []

    thinking_text = item.get("thinking", "").strip()
    if not thinking_text:
        return []

    lines = [
        "<details>",
        "<summary>Thinking</summary>",
        "",
        thinking_text,
        "",
        "</details>",
        "",
    ]
    return lines


def render_voice_note(
    item: dict, options: RenderOptions, citations: CitationCollector
) -> list[str]:
    """Render a voice note content item."""
    title = item.get("title", "Voice Note")
    text = item.get("text", "").strip()
    if not text:
        return []

    lines = [f"**[Voice Note: {title}]**", "", text, ""]
    return lines


def render_tool_use(
    item: dict, options: RenderOptions, citations: CitationCollector
) -> list[str]:
    """Render a tool_use content item."""
    if not options.include_tools:
        return []

    tool_name = item.get("name", "unknown_tool")
    tool_input = item.get("input", {})

    lines = [f"**Tool: {tool_name}**"]

    if tool_name == "web_search":
        query = tool_input.get("query", "")
        lines.append(f"- Query: `{query}`")

    elif tool_name == "artifacts":
        command = tool_input.get("command", "")
        artifact_id = tool_input.get("id", "")
        title = tool_input.get("title", "")
        artifact_type = tool_input.get("type", "")
        language = tool_input.get("language", "")

        lines.append(f"- Command: `{command}`")
        if artifact_id:
            lines.append(f"- ID: `{artifact_id}`")
        if title:
            lines.append(f"- Title: {title}")
        if artifact_type:
            lines.append(f"- Type: {artifact_type}")
        if language:
            lines.append(f"- Language: {language}")

        # Show content for create/rewrite if verbose
        if options.verbose_tools and command in ("create", "rewrite"):
            content = tool_input.get("content", "")
            if content:
                lang_hint = language or ""
                lines.append("")
                lines.append(f"```{lang_hint}")
                lines.append(content)
                lines.append("```")

        # Show update diff if verbose
        if options.verbose_tools and command == "update":
            old_str = tool_input.get("old_str", "")
            new_str = tool_input.get("new_str", "")
            if old_str or new_str:
                lines.append("")
                lines.append("```diff")
                if old_str:
                    for line in old_str.split("\n")[:10]:
                        lines.append(f"- {line}")
                if new_str:
                    for line in new_str.split("\n")[:10]:
                        lines.append(f"+ {line}")
                lines.append("```")

    elif tool_name in ("create_file", "file_create"):
        path = tool_input.get("path", "")
        description = tool_input.get("description", "")
        lines.append(f"- Path: `{path}`")
        if description:
            lines.append(f"- Description: {description}")
        if options.verbose_tools:
            content = tool_input.get("file_text") or tool_input.get("content", "")
            if content:
                lines.append("")
                lines.append("```")
                lines.append(content[:2000])
                if len(content) > 2000:
                    lines.append("... (truncated)")
                lines.append("```")

    elif tool_name == "str_replace":
        path = tool_input.get("path", "")
        lines.append(f"- Path: `{path}`")
        if options.verbose_tools:
            old_str = tool_input.get("old_str", "")
            new_str = tool_input.get("new_str", "")
            lines.append("")
            lines.append("```diff")
            if old_str:
                for line in old_str.split("\n")[:5]:
                    lines.append(f"- {line}")
            if new_str:
                for line in new_str.split("\n")[:5]:
                    lines.append(f"+ {line}")
            lines.append("```")

    else:
        # Generic tool display
        if options.verbose_tools and tool_input:
            lines.append("")
            lines.append("```json")
            lines.append(json.dumps(tool_input, indent=2)[:1000])
            lines.append("```")
        elif tool_input:
            # Show first few key-value pairs
            for key, value in list(tool_input.items())[:3]:
                val_str = str(value)
                if len(val_str) > 50:
                    val_str = val_str[:50] + "..."
                lines.append(f"- {key}: {val_str}")

    lines.append("")
    return lines


def render_tool_result(
    item: dict, options: RenderOptions, citations: CitationCollector
) -> list[str]:
    """Render a tool_result content item."""
    if not options.include_tools:
        return []

    tool_name = item.get("name", "unknown_tool")
    is_error = item.get("is_error", False)
    content = item.get("content", "")

    status = "Error" if is_error else "Result"
    lines = [f"**Tool {status}: {tool_name}**"]

    # Only show content for errors or if verbose
    if is_error and content:
        content_str = str(content)[:500] if content else ""
        if content_str:
            lines.append("")
            lines.append("```")
            lines.append(content_str)
            lines.append("```")
    elif options.verbose_tools and content:
        content_str = str(content)
        if len(content_str) > 2000:
            content_str = content_str[:2000] + "\n... (truncated)"
        lines.append("")
        lines.append("```")
        lines.append(content_str)
        lines.append("```")

    lines.append("")
    return lines


# Dispatcher mapping content types to renderers
CONTENT_RENDERERS: dict[str, Callable] = {
    "text": render_text,
    "thinking": render_thinking,
    "voice_note": render_voice_note,
    "tool_use": render_tool_use,
    "tool_result": render_tool_result,
}


def render_content_item(
    item: dict, options: RenderOptions, citations: CitationCollector
) -> list[str]:
    """Dispatch to appropriate renderer based on content type."""
    content_type = item.get("type", "text")
    renderer = CONTENT_RENDERERS.get(content_type, render_text)
    return renderer(item, options, citations)
