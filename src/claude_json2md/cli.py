import typer
from pathlib import Path
from typing import Optional
import logging

from .log_setup import setup_logging, DEFAULT_LOG_FILENAME
from .converter import json_to_markdown

app = typer.Typer()

logger = logging.getLogger("converter_app")  # Or a more specific name like "cli_app"


@app.command()
def main(
    json_input_file: Path = typer.Argument(
        ...,
        help="Path to the input JSON file.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    markdown_output_directory: Path = typer.Argument(
        Path("markdown_conversations"),  # Default output directory
        help="Directory to save the output Markdown files.",
        file_okay=False,
        dir_okay=True,
        writable=True,
        resolve_path=True,
    ),
    limit: Optional[int] = typer.Option(
        None,
        "--limit",
        "-l",
        help="Limit the number of conversations to process. Processes all by default.",
        min=0,  # Ensure limit is non-negative if provided
    ),
    log_path: Optional[Path] = typer.Option(
        None,
        "--log-path",
        help=(
            f"Specify a custom path for the log file. "
            f"If a directory, '{DEFAULT_LOG_FILENAME}' will be used. "
            f"Defaults to a standard user log directory."
        ),
        file_okay=True,
        dir_okay=True,
        writable=True,
        resolve_path=True,
    ),
):
    """
    Converts conversations from a JSON file to individual Markdown files.
    """
    setup_logging(log_path_override=log_path)  # Call setup_logging early

    logger.info(
        f"Application started. Input: '{json_input_file}', Output dir: '{markdown_output_directory}', Limit: {limit}, LogPath: {log_path if log_path else 'Default'}"
    )

    # markdown_output_directory is already resolved by Typer, but ensuring it exists is good practice.
    # Typer's writable=True for a directory argument doesn't create it; resolve_path=True resolves it.
    # We still need to create it if it doesn't exist.
    try:
        markdown_output_directory.mkdir(parents=True, exist_ok=True)
        logger.info(
            f"Ensured output directory exists: {markdown_output_directory.resolve()}"
        )
    except OSError as e:
        logger.error(
            f"Error creating output directory {markdown_output_directory}: {e}"
        )
        # Depending on desired behavior, you might want to raise typer.Exit(code=1) here
        return  # Exit if directory cannot be created

    logger.info(
        f"Input: '{json_input_file.name}'. Output directory: '{markdown_output_directory}'."
    )

    json_to_markdown(json_input_file, markdown_output_directory, limit=limit)
    logger.info("Application finished.")


if __name__ == "__main__":
    app()
