import json
import logging
import logging.config
from pathlib import Path
from typing import Optional
from platformdirs import user_log_dir

# --- Constants for Logging ---
APP_NAME = "JSONToMarkdownConverter"
APP_AUTHOR = "ConverterApp"  # Can be your organization or a generic author name
DEFAULT_LOG_FILENAME = "converter.log"


# --- Logging Setup ---
def setup_logging(log_path_override: Optional[Path] = None):
    """Loads logging configuration and sets up log file path."""

    config_file = Path(__file__).parent / "logging_config.json"

    log_file_path_to_log = ""
    is_custom_path = False

    # Check if log_path_override is a Path or None
    if log_path_override is not None and not isinstance(log_path_override, Path):
        log_path_override = None

    if not config_file.exists():
        logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
        logging.error(
            f"CRITICAL: logging_config.json not found at {config_file}. Basic emergency logging enabled."
        )
        # Attempt to set up a basic file logger even if config is missing, for critical errors
        try:
            emergency_log_dir = (
                Path(user_log_dir(APP_NAME, appauthor=APP_AUTHOR)) / "emergency_logs"
            )
            emergency_log_dir.mkdir(parents=True, exist_ok=True)
            emergency_log_file = emergency_log_dir / DEFAULT_LOG_FILENAME
            fh = logging.FileHandler(emergency_log_file)
            fh.setLevel(logging.WARNING)
            fh.setFormatter(
                logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            )
            logging.getLogger().addHandler(fh)
            logging.warning(f"Logging emergency output to {emergency_log_file}")
            log_file_path_to_log = str(emergency_log_file)
        except Exception as e_log:
            logging.error(f"Failed to set up emergency file logger: {e_log}")
        return

    with open(config_file, "r") as f:
        config = json.load(f)

    if log_path_override:
        is_custom_path = True
        if log_path_override.is_dir():
            actual_log_file_path = log_path_override / DEFAULT_LOG_FILENAME
            log_path_override.mkdir(parents=True, exist_ok=True)
        else:
            actual_log_file_path = log_path_override
            actual_log_file_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        # Default to user-specific log directory
        platform_log_dir = Path(user_log_dir(APP_NAME, appauthor=APP_AUTHOR))
        platform_log_dir.mkdir(parents=True, exist_ok=True)
        actual_log_file_path = platform_log_dir / DEFAULT_LOG_FILENAME

    log_file_path_to_log = str(actual_log_file_path)  # Store for logging after config

    if "handlers" in config and "file" in config["handlers"]:
        config["handlers"]["file"]["filename"] = str(actual_log_file_path)
    else:
        # Log this issue using a basic logger setup before dictConfig potentially fails or changes things
        temp_logger = logging.getLogger("setup_logging_warning")
        temp_logger.addHandler(logging.StreamHandler())  # Ensure it goes somewhere
        temp_logger.warning(
            "Could not find 'file' handler in logging_config.json to set filename. File logging may not work as expected."
        )

    try:
        logging.config.dictConfig(config)
        # Now the main logger is configured. Get it and log the path.
        configured_logger = logging.getLogger("converter_app")
        if is_custom_path:
            configured_logger.info(
                f"Custom log path specified. File logging to: {log_file_path_to_log}"
            )
        else:
            configured_logger.info(f"Default file logging to: {log_file_path_to_log}")
    except Exception as e_dict_config:
        # Fallback if dictConfig fails catastrophically
        logging.basicConfig(level=logging.ERROR, format="%(levelname)s: %(message)s")
        logging.error(
            f"CRITICAL: Failed to apply logging configuration from {config_file}. Error: {e_dict_config}"
        )
        if log_file_path_to_log:  # If we determined a path, mention it
            logging.error(f"Intended log file path was: {log_file_path_to_log}")
