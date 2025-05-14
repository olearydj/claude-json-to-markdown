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

## Usage

The quickest way to use `cj2md` without a full local installation is with `uvx`. If you plan to use the tool regularly or contribute to its development, see the [Installation](#installation) section below.

### Run with `uvx`

`uvx` temporarily installs the package and its dependencies in an isolated environment and runs the specified command:

```bash
uvx cj2md [OPTIONS] JSON_INPUT_FILE [MARKDOWN_OUTPUT_DIRECTORY]
```

Arguments and Options:

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

## Installation

If you prefer to install `cj2md` locally (e.g., for development), follow these instructions:

1.  **Clone the repository (if you haven't already)**
   
    ```bash
    git clone <your-repository-url> # Replace with your actual repo URL
    cd claude-json-to-markdown
    ```

2.  **Install the package with its dependencies using `uv`:**

    ```bash
    uv sync
    ```

    The `uv sync` command will create a virtual environment (in `.venv` by default) and install all runtime and development dependencies defined in `pyproject.toml`. It also installs the package in editable mode, so changes to the source code are immediately available.

3. **Run the tool with `uv`"**
   
   ```bash
   uv run cj2md ...
   ```

If you prefer to use `pip`, you probably know the drill:

```bash
git clone <your-repository-url>  # Replace with actual repo
cd claude-json-to-markdown
python -m venv .venv
source .venv/bin/activate
pip install .
pip install .[test]
```

## Running Tests

To run the test suite (which includes unit and integration tests):

1.  Ensure you have installed the test dependencies, which `uv sync` handles automagically.
2.  Navigate to the project root directory.
3.  Run pytest using `uv`:

    ```bash
    uv run pytest
    ```

If you are still using `pip`:

```bash
source .venv/bin/activate
pytest
```

## Logging Behavior

- The application uses Python's standard `logging` module, along with some [`rich` goodness](https://github.com/Textualize/rich).
- By default (if `logging_config.json` is not found alongside `log_setup.py` in the installed package or during development in `src/claude_json2md/`), a basic emergency logger is set up for critical errors, and platform-specific user log directories are used for regular file logging.
- If `logging_config.json` *is* present (expected to be in `src/claude_json2md/` alongside `log_setup.py`), it defines the logging format, levels, and handlers. The default configuration includes a console handler and a file handler.
- The `DEFAULT_LOG_FILENAME` is `converter.log`.
- The `APP_NAME` for `platformdirs` is "JSONToMarkdownConverter" and `APP_AUTHOR` is "ConverterApp" (this can be customized in `src/claude_json2md/log_setup.py`).

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

## License

This project is licensed under the terms of the MIT License.
