from pathlib import Path
import json

# Functions to be tested
from claude_json2md.converter import (
    create_slug,
    load_and_validate_conversations,
    generate_filename,
    generate_markdown_content,
    write_markdown_file,
    has_meaningful_content,
)
from claude_json2md.renderers import RenderOptions

# --- Tests for create_slug ---


def test_create_slug_basic():
    assert create_slug("Simple Test String") == "simple-test-string"


def test_create_slug_special_chars_and_spaces():
    assert (
        create_slug("  Test with !@#$ and   multiple spaces  ")
        == "test-with-and-multiple-spaces"
    )


def test_create_slug_empty_input():
    assert create_slug("") == "untitled"


def test_create_slug_becomes_empty_after_processing():
    assert create_slug("!@#$%^") == "untitled"


def test_create_slug_max_length_truncation():
    long_string = "This is a very long string that will definitely exceed the fifty character limit"
    assert (
        create_slug(long_string, max_length=20) == "this-is-a-very-long"
    )  # Expected: 20 chars


def test_create_slug_leading_trailing_hyphens_internal():
    # This tests if a string that *could* produce leading/trailing hyphens internally is handled
    assert create_slug(" ---test--- ") == "test"


def test_create_slug_all_hyphens_and_spaces():
    assert create_slug(" - - - ") == "untitled"


def test_create_slug_only_special_chars_and_some_spaces():
    assert create_slug(" !@# $%^ ") == "untitled"


# --- Tests for load_and_validate_conversations ---


def test_load_and_validate_valid_json(mocker):
    sample_data = [{"name": "Test1"}, {"name": "Test2"}]
    mock_file_content = json.dumps(sample_data)
    mocker.patch("pathlib.Path.open", mocker.mock_open(read_data=mock_file_content))
    mocker.patch(
        "json.load", return_value=sample_data
    )  # Ensure json.load is also consistently mocked

    result = load_and_validate_conversations(Path("dummy.json"))
    assert result == sample_data


def test_load_and_validate_file_not_found(mocker, caplog):
    mocker.patch("pathlib.Path.open", side_effect=FileNotFoundError("File not found"))

    result = load_and_validate_conversations(Path("nonexistent.json"))
    assert result is None
    assert "Error: Input JSON file not found" in caplog.text


def test_load_and_validate_invalid_json(mocker, caplog):
    mocker.patch(
        "pathlib.Path.open", mocker.mock_open(read_data='[{"name": "Test1"')
    )  # Malformed JSON string, but valid Python string
    mocker.patch("json.load", side_effect=json.JSONDecodeError("dummy error", "doc", 0))

    result = load_and_validate_conversations(Path("bad.json"))
    assert result is None
    assert "Error: Could not decode JSON from" in caplog.text


def test_load_and_validate_json_not_a_list(mocker, caplog):
    sample_data = {"name": "Not a list"}
    mock_file_content = json.dumps(sample_data)
    mocker.patch("pathlib.Path.open", mocker.mock_open(read_data=mock_file_content))
    mocker.patch("json.load", return_value=sample_data)

    result = load_and_validate_conversations(Path("notalist.json"))
    assert result is None
    assert (
        "Error: The JSON file's top-level structure is not a list of conversations."
        in caplog.text
    )


def test_load_and_validate_other_exception(mocker, caplog):
    mocker.patch("pathlib.Path.open", side_effect=OSError("Disk read error"))
    result = load_and_validate_conversations(Path("othererror.json"))
    assert result is None
    assert "An unexpected error occurred while reading" in caplog.text


# --- Tests for generate_filename ---


def test_generate_filename_standard():
    conv_data = {"uuid": "abc-123-def", "created_at": "2023-07-15T10:00:00Z"}
    conv_name = "My Awesome Conversation"
    assert (
        generate_filename(conv_data, conv_name)
        == "2023-07-15_my-awesome-conversation_abc.md"
    )


def test_generate_filename_created_at_na():
    conv_data = {"uuid": "xyz-789", "created_at": "N/A"}
    conv_name = "Another One"
    assert generate_filename(conv_data, conv_name) == "unknown-date_another-one_xyz.md"


def test_generate_filename_uuid_no_hyphen():
    conv_data = {"uuid": "fulluuid", "created_at": "2023-07-15T10:00:00Z"}
    conv_name = "No Hyphen UUID"
    assert (
        generate_filename(conv_data, conv_name)
        == "2023-07-15_no-hyphen-uuid_fulluuid.md"
    )


def test_generate_filename_empty_name():
    conv_data = {"uuid": "emptyname-uuid", "created_at": "2023-07-15T10:00:00Z"}
    conv_name = ""  # create_slug will turn this into "untitled"
    assert generate_filename(conv_data, conv_name) == "2023-07-15_untitled_emptyname.md"


# --- Tests for generate_markdown_content ---


def test_generate_markdown_content_basic():
    conv_data = {
        "uuid": "conv-uuid-001",
        "name": "Greeting Exchange",  # name in conv_data for consistency, though conv_name param is used
        "created_at": "2023-01-01T10:00:00Z",
        "updated_at": "2023-01-01T11:00:00Z",
        "chat_messages": [
            {
                "sender": "User",
                "created_at": "2023-01-01T10:05:00Z",
                "text": "Hello there!",
            },
            {
                "sender": "AI",
                "created_at": "2023-01-01T10:06:00Z",
                "content": [{"type": "text", "text": "Hi User!"}],
            },
        ],
    }
    conv_name = "Greeting Exchange"
    md_lines = generate_markdown_content(conv_data, conv_name)

    assert "# Conversation: Greeting Exchange\n" in md_lines
    assert "**UUID:** conv-uuid-001" in md_lines
    assert "**Created At:** 2023-01-01T10:00:00Z" in md_lines
    assert "**Updated At:** 2023-01-01T11:00:00Z" in md_lines
    assert "## Messages\n" in md_lines
    assert "---" in md_lines
    assert "**Sender:** User" in md_lines
    assert "Hello there!" in md_lines
    assert "**Sender:** Ai" in md_lines  # Note: .capitalize() behavior
    assert "Hi User!" in md_lines


def test_generate_markdown_content_no_messages():
    conv_data = {
        "uuid": "conv-uuid-002",
        "name": "Empty Talk",
        "created_at": "2023-01-02T00:00:00Z",
        "updated_at": "2023-01-02T00:00:00Z",
        "chat_messages": [],
    }
    conv_name = "Empty Talk"
    md_lines = generate_markdown_content(conv_data, conv_name)

    assert "## Messages\n" in md_lines
    message_section_index = md_lines.index("## Messages\n")
    # Ensure no message separators or content after "## Messages\n"
    assert all(
        not line.startswith("---") and not line.startswith("**Sender:**")
        for line in md_lines[message_section_index + 1 :]
    )


def test_generate_markdown_content_with_attachments():
    conv_data = {
        "uuid": "conv-uuid-003",
        "name": "File Share",
        "created_at": "2023-01-03T00:00:00Z",
        "updated_at": "2023-01-03T00:00:00Z",
        "chat_messages": [
            {
                "sender": "User",
                "text": "See attached.",
                "created_at": "N/A",
                "files": [{"file_name": "doc1.pdf"}, {"file_name": "image.png"}],
            }
        ],
    }
    conv_name = "File Share"
    md_lines = generate_markdown_content(conv_data, conv_name)
    assert "**Attachments:** doc1.pdf, image.png" in md_lines


def test_generate_markdown_content_sparse_message_data():
    conv_data = {
        "uuid": "conv-uuid-004",
        "name": "Sparse Message",
        "created_at": "N/A",
        "updated_at": "N/A",
        "chat_messages": [
            {"created_at": "A while ago"}
        ],  # No sender, no text, no content
    }
    conv_name = "Sparse Message"
    md_lines = generate_markdown_content(conv_data, conv_name)

    assert "**Sender:** Unknown sender" in md_lines
    assert "**Timestamp:** A while ago" in md_lines
    # Empty message should still have blank line for content area
    assert "" in md_lines  # At least one empty string for blank line


# --- Tests for write_markdown_file ---


def test_write_markdown_file_success(mocker):
    mock_file = mocker.mock_open()
    mocker.patch("pathlib.Path.open", mock_file)

    filepath = Path("test_output.md")
    content_lines = ["Line1", "Second Line"]

    success = write_markdown_file(filepath, content_lines, "Test Conv", "test-uuid")

    assert success is True
    mock_file.assert_called_once_with("w", encoding="utf-8")
    mock_file().write.assert_called_once_with("Line1\nSecond Line")


def test_write_markdown_file_io_error(mocker, caplog):
    mocker.patch("pathlib.Path.open", side_effect=IOError("Disk full"))

    filepath = Path("test_output_fail.md")
    content_lines = ["Line1"]

    success = write_markdown_file(
        filepath, content_lines, "Test Conv Fail", "test-uuid-fail"
    )

    assert success is False
    assert "Error writing Markdown file" in caplog.text
    assert "Disk full" in caplog.text


def test_write_markdown_file_other_exception(mocker, caplog):
    mocker.patch("pathlib.Path.open", side_effect=Exception("Unexpected FS error"))

    filepath = Path("test_output_unexpected.md")
    content_lines = ["Line1"]

    success = write_markdown_file(
        filepath, content_lines, "Test Conv Unexp", "test-uuid-unexp"
    )

    assert success is False
    assert "An unexpected error occurred while writing" in caplog.text
    assert "Unexpected FS error" in caplog.text


# --- Tests for has_meaningful_content ---


def test_has_meaningful_content_with_text():
    messages = [{"text": "Hello world"}]
    assert has_meaningful_content(messages) is True


def test_has_meaningful_content_with_content_text():
    messages = [{"content": [{"type": "text", "text": "Hello"}]}]
    assert has_meaningful_content(messages) is True


def test_has_meaningful_content_with_thinking():
    messages = [{"content": [{"type": "thinking", "thinking": "Let me think..."}]}]
    assert has_meaningful_content(messages) is True


def test_has_meaningful_content_with_voice_note():
    messages = [{"content": [{"type": "voice_note", "text": "Spoken words"}]}]
    assert has_meaningful_content(messages) is True


def test_has_meaningful_content_with_tool_use():
    messages = [{"content": [{"type": "tool_use", "name": "web_search"}]}]
    assert has_meaningful_content(messages) is True


def test_has_meaningful_content_empty():
    messages = [{"text": "", "content": []}]
    assert has_meaningful_content(messages) is False


def test_has_meaningful_content_whitespace_only():
    messages = [{"text": "   ", "content": [{"type": "text", "text": "  \n  "}]}]
    assert has_meaningful_content(messages) is False


# --- Tests for generate_markdown_content with new features ---


def test_generate_markdown_content_with_summary():
    conv_data = {
        "uuid": "conv-summary-001",
        "name": "Test with Summary",
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T11:00:00Z",
        "summary": "This is a conversation about testing.",
        "chat_messages": [{"sender": "human", "text": "Hello"}],
    }
    md_lines = generate_markdown_content(conv_data, "Test with Summary")
    assert "**Summary:**" in md_lines
    assert "> This is a conversation about testing." in md_lines


def test_generate_markdown_content_no_summary_option():
    conv_data = {
        "uuid": "conv-summary-002",
        "name": "Test with Summary Disabled",
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T11:00:00Z",
        "summary": "This should not appear.",
        "chat_messages": [{"sender": "human", "text": "Hello"}],
    }
    options = RenderOptions(include_summary=False)
    md_lines = generate_markdown_content(
        conv_data, "Test with Summary Disabled", options
    )
    assert "**Summary:**" not in md_lines
    assert "This should not appear." not in md_lines


def test_generate_markdown_content_multiple_content_items():
    conv_data = {
        "uuid": "conv-multi-001",
        "name": "Multi Content",
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T11:00:00Z",
        "chat_messages": [
            {
                "sender": "assistant",
                "created_at": "2024-01-01T10:01:00Z",
                "content": [
                    {"type": "thinking", "thinking": "Let me consider..."},
                    {"type": "text", "text": "Here is my answer."},
                ],
            }
        ],
    }
    md_lines = generate_markdown_content(conv_data, "Multi Content")
    assert "<summary>Thinking</summary>" in md_lines
    assert "Let me consider..." in md_lines
    assert "Here is my answer." in md_lines


def test_generate_markdown_content_tool_use():
    conv_data = {
        "uuid": "conv-tool-001",
        "name": "Tool Test",
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T11:00:00Z",
        "chat_messages": [
            {
                "sender": "assistant",
                "created_at": "2024-01-01T10:01:00Z",
                "content": [
                    {
                        "type": "tool_use",
                        "name": "web_search",
                        "input": {"query": "python dataclasses"},
                    }
                ],
            }
        ],
    }
    md_lines = generate_markdown_content(conv_data, "Tool Test")
    md_text = "\n".join(md_lines)
    assert "**Tool: web_search**" in md_text
    assert "Query: `python dataclasses`" in md_text


def test_generate_markdown_content_voice_note():
    conv_data = {
        "uuid": "conv-voice-001",
        "name": "Voice Test",
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T11:00:00Z",
        "chat_messages": [
            {
                "sender": "human",
                "created_at": "2024-01-01T10:01:00Z",
                "content": [
                    {
                        "type": "voice_note",
                        "title": "Quick question",
                        "text": "What is the meaning of life?",
                    }
                ],
            }
        ],
    }
    md_lines = generate_markdown_content(conv_data, "Voice Test")
    assert "**[Voice Note: Quick question]**" in md_lines
    assert "What is the meaning of life?" in md_lines


def test_generate_markdown_content_citations():
    conv_data = {
        "uuid": "conv-cite-001",
        "name": "Citation Test",
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T11:00:00Z",
        "chat_messages": [
            {
                "sender": "assistant",
                "created_at": "2024-01-01T10:01:00Z",
                "content": [
                    {
                        "type": "text",
                        "text": "According to the documentation...",
                        "citations": [{"url": "https://example.com/docs"}],
                    }
                ],
            }
        ],
    }
    md_lines = generate_markdown_content(conv_data, "Citation Test")
    md_text = "\n".join(md_lines)
    assert "## References" in md_text
    assert "https://example.com/docs" in md_text


def test_generate_markdown_content_no_thinking_option():
    conv_data = {
        "uuid": "conv-opt-001",
        "name": "Options Test",
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T11:00:00Z",
        "chat_messages": [
            {
                "sender": "assistant",
                "created_at": "2024-01-01T10:01:00Z",
                "content": [
                    {"type": "thinking", "thinking": "Secret thoughts"},
                    {"type": "text", "text": "Public answer"},
                ],
            }
        ],
    }
    options = RenderOptions(include_thinking=False)
    md_lines = generate_markdown_content(conv_data, "Options Test", options)
    assert "Secret thoughts" not in md_lines
    assert "Public answer" in md_lines


def test_generate_markdown_content_backward_compatible():
    """Test that old format without type field still works."""
    conv_data = {
        "uuid": "conv-old-001",
        "name": "Old Format",
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T11:00:00Z",
        "chat_messages": [
            {
                "sender": "user",
                "created_at": "2024-01-01T10:01:00Z",
                "content": [{"text": "Old style without type field"}],
            }
        ],
    }
    md_lines = generate_markdown_content(conv_data, "Old Format")
    assert "Old style without type field" in md_lines
