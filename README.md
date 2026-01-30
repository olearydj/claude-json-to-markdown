# Claude JSON to Markdown Converter (`cj2md`)

A command-line tool that converts [Anthropic Claude](https://www.anthropic.com/) conversation exports to Markdown files.

## Installation

```bash
# Run directly (recommended)
uvx cj2md <input.json> [output_dir]

# Or install globally
uv tool install claude-json-to-markdown

# Or add to a project
uv add claude-json-to-markdown
```

## Exporting Your Data

Follow [Anthropic's export guide](https://support.anthropic.com/en/articles/9450526-how-can-i-export-my-claude-ai-data):

1. Click your initials (lower left) > Settings > Privacy > Export data
2. Download link arrives via email

## Usage

```bash
cj2md [OPTIONS] JSON_INPUT_FILE [MARKDOWN_OUTPUT_DIRECTORY]
```

### Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `JSON_INPUT_FILE` | Path to exported JSON file | Required |
| `MARKDOWN_OUTPUT_DIRECTORY` | Output directory for .md files | `markdown_conversations` |

### Options

| Option | Description |
|--------|-------------|
| `-l, --limit INT` | Limit number of conversations processed |
| `--log-path PATH` | Custom log file path |
| `--no-summary` | Omit conversation summary from header |
| `--no-thinking` | Omit Claude's thinking blocks |
| `--no-citations` | Omit References section with URLs |
| `--no-tools` | Omit tool usage (web_search, artifacts, etc.) |
| `--verbose-tools` | Show full tool inputs/outputs |

### Example

```bash
uvx cj2md conversations.json ./output --limit 50 --no-thinking
```

## Output Format

Each conversation becomes a Markdown file named `YYYY-MM-DD_slugified-name_uuid.md` containing:

- **Header**: UUID, name, timestamps, optional summary
- **Messages**: Sender, timestamp, content, attachments
- **Thinking blocks**: Claude's reasoning (unless `--no-thinking`)
- **Tool usage**: Web searches, artifacts, file operations (unless `--no-tools`)
- **References**: Citation URLs (unless `--no-citations`)

Conversations with no name or empty content are automatically skipped.

## Development

```bash
git clone https://github.com/olearydj/claude-json-to-markdown.git
cd claude-json-to-markdown
uv sync
uv run pytest
```

## Limitations

- Project data from exports is not processed (no clear way to link conversations to projects)
- Artifact content is shown as operations (create/update/rewrite) rather than reconstructed final state

## License

MIT

## Links

- [Issues](https://github.com/olearydj/claude-json-to-markdown/issues)
- [PyPI](https://pypi.org/project/claude-json-to-markdown/)
