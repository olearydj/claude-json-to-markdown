# Claude JSON to Markdown Converter (`cj2md`)

`cj2md` is a command-line tool that converts conversation the data exported from [Anthropic's Claude](https://www.anthropic.com/) into Markdown. Each conversation is saved as a separate `.md` file, making it easier to read, archive, or process further.

Follow [these steps](https://support.anthropic.com/en/articles/9450526-how-can-i-export-my-claude-ai-data) to export your data:

1. Click on your initials in the lower left corner of your account.
2. Select "Settings" from the menu.
3. Navigate to the "Privacy" section.
4. Click the "Export data" button.

Once the export has been processed, you will receive a download link via the email address associated with your account.

## Features

- **Direct JSON Input:** Processes JSON files containing a list of conversation objects.
- **Individual Markdown Files:** Each conversation in the input JSON is converted into its own Markdown file.
- **Structured Markdown Output:**
    - Conversation metadata (UUID, name, creation/update timestamps) is included at the top of each file.
    - Messages are clearly separated, showing the sender, timestamp, and message content.
    - Attached files within messages are listed.
- **Smart Filename Generation:** Output Markdown filenames are generated based on the conversation's creation date, a slugified version of its name, and a short UUID for uniqueness (e.g., `YYYY-MM-DD_conversation-name_uuid-prefix.md`).
- **Skipping Logic:**
    - Automatically skips conversations with no name.
    - Automatically skips conversations that have no messages or where all messages are empty.
- **Processing Limit:** Option to limit the number of conversations processed from the input file using the `--limit` / `-l` flag.
- **Customizable Logging:**
    - Detailed logging of operations, including processed files, skipped conversations, and errors.
    - Log output path can be specified using the `--log-path` flag. If a directory is provided, a default log filename (`converter.log`) is used. Logs are otherwise placed in a standard user log directory.
    - Uses a `logging_config.json` for configurable log formatting and levels (if present next to the `log_setup.py` module).
- **Command-Line Interface:** Simple and straightforward CLI powered by Typer.

## Syntax

```bash
cj2md [OPTIONS] JSON_INPUT_FILE [MARKDOWN_OUTPUT_DIRECTORY]
```

*   `JSON_INPUT_FILE`: (Required) Path to the input JSON file containing the conversation data.
*   `MARKDOWN_OUTPUT_DIRECTORY`: (Required) Path to the directory where the output Markdown files will be saved. If the directory doesn't exist, it will be created.
*   `--limit INTEGER`, `-l INTEGER`: Limit the number of conversations to process. Processes all by default.
*   `--log-path PATH`: Specify a custom path for the log file.
    *   If a directory path is provided, `converter.log` will be created within that directory.
    *   If a full file path is provided, that file will be used for logging.
    *   If omitted, logs are placed in a default user-specific log directory (e.g., `~/Library/Logs/JSONToMarkdownConverter/converter.log` on macOS).
*   `--help`: Show the help message and exit.

**Example:**

```bash
uvx cj2md data/conversations.json output_markdown --limit 50 --log-path ./logs/conversion.log
```

This command will:
1.  Read conversations from `data/conversations.json`.
2.  Process a maximum of 50 conversations.
3.  Save the resulting Markdown files into the `output_markdown` directory (creating it if it doesn't exist).
4.  Write log messages to `./logs/conversion.log`.

## Usage

> [!NOTE]
> This project uses and recommends [`uv`](https://github.com/astral-sh/uv) for Python package and project management.
> Not just (way) faster, (way) better.

### Run from PyPI with `pipx` or `uvx`

This is the quickest and recommended way to use `cj2md` without a full local installation. `pipx` and `uvx` (an alias for `uv tool run`) install the package and its dependencies in an isolated environment and run the specified command. This keeps your global Python environment clean and allows you to use `cj2md` as a stand alone tool.

**Using `uvx`:**

```bash
uvx cj2md [OPTIONS] JSON_INPUT_FILE [MARKDOWN_OUTPUT_DIRECTORY]
```

**Using `pipx`:**

```bash
pipx run cj2md [OPTIONS] JSON_INPUT_FILE [MARKDOWN_OUTPUT_DIRECTORY]
```

### Install PyPI Package into a Virtual Environment

If you prefer to install `cj2md` as a regular package into a specific virtual environment (e.g., to use it as part of a larger project or script), you can do so using `uv` or `pip`.

**The `uv` way:**

```bash
# Assumes you are working in a project managed with pyproject.toml
uv add claude-json-to-markdown 
```

**The `pip` way:**

```bash
# In your active virtual environment
pip install claude-json-to-markdown
```

## Project Structure

The project is structured as an installable Python package:

-   `src/claude_json2md/`: Contains the main application source code.
    -   `cli.py`: Command-line interface logic using Typer.
    -   `converter.py`: Core JSON to Markdown conversion functions.
    -   `log_setup.py`: Logging configuration and setup.
    -   `logging_config.json`: (Optional) Configuration file for Python's logging system.
-   `tests/`: Contains unit and integration tests.
-   `pyproject.toml`: Defines project metadata, dependencies, and build system configuration.

This structure allows the tool to be installed and run as a command-line utility (`cj2md`).

## Logging Behavior

- The application uses Python's standard `logging` module, along with some [`rich` goodness](https://github.com/Textualize/rich).
- By default (if `logging_config.json` is not found alongside `log_setup.py` in the installed package or during development in `src/claude_json2md/`), a basic emergency logger is set up for critical errors, and platform-specific user log directories are used for regular file logging.
- If `logging_config.json` *is* present (expected to be in `src/claude_json2md/` alongside `log_setup.py`), it defines the logging format, levels, and handlers. The default configuration includes a console handler and a file handler.
- The `DEFAULT_LOG_FILENAME` is `converter.log`.
- The `APP_NAME` for `platformdirs` is "JSONToMarkdownConverter" and `APP_AUTHOR` is "ConverterApp" (this can be customized in `src/claude_json2md/log_setup.py`).

## Changelog

### 0.1.0 (2025-05-15)

- Initial release
- Core functionality for converting Claude JSON exports to Markdown
- Support for processing multiple conversations from a single JSON file
- Command-line interface with options for limiting processing and custom logging
- Intelligent naming of output files based on conversation metadata
- Comprehensive logging for tracking conversion progress and issues

## Limitations

- `cj2md` does not support the projects data included with the data Anthropic exports. There is not obvious way to link conversations to projects, though it seems that the conversations data includes all those related to projects.
- `cj2md` exports to not include the internal "thinking" dialogue sometimes used by Claude. This data is included in the conversations data, but isn't currently captured in `cj2md` output.

## Issues & Contributions

### Reporting Issues

If you encounter any problems with the tool, please [open an issue](https://github.com/olearydj/claude-json-to-markdown/issues) on GitHub with:

- A clear description of the problem
- Steps to reproduce the issue
- Expected vs. actual behavior
- Your environment details (OS, Python version)
- Sample data (sanitized appropriately!)

### Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository** and clone your fork
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes** and add tests if applicable
4. **Run the tests** to ensure everything works: `uv run pytest`
5. **Commit your changes**: `git commit -m "Add your feature description"`
6. **Push to your branch**: `git push origin feature/your-feature-name`
7. **Create a pull request** from your fork to the main repository

Please follow the existing code style and include appropriate tests for new functionality. The development setup is described above.

## License

This project is licensed under the terms of the MIT License.
