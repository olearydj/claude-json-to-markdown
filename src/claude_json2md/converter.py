import json
from pathlib import Path
from typing import Optional
import re
import logging

logger = logging.getLogger("converter_app")


def load_and_validate_conversations(json_file_path: Path) -> Optional[list]:
    """Loads JSON data from a file and performs initial validation."""
    try:
        with json_file_path.open("r", encoding="utf-8") as f:
            conversations = json.load(f)
        logger.debug(f"Successfully loaded JSON data from {json_file_path}")
    except FileNotFoundError:
        logger.error(f"Error: Input JSON file not found at {json_file_path}")
        return None
    except json.JSONDecodeError:
        logger.error(
            f"Error: Could not decode JSON from {json_file_path}. Please ensure it's valid JSON."
        )
        return None
    except Exception as e:
        logger.exception(
            f"An unexpected error occurred while reading {json_file_path}: {e}"
        )
        return None

    if not isinstance(conversations, list):
        logger.error(
            "Error: The JSON file's top-level structure is not a list of conversations."
        )
        return None
    return conversations


def generate_filename(conversation_data: dict, conv_name: str) -> str:
    """Generates a unique filename for the Markdown file."""
    conv_uuid = conversation_data.get("uuid", "unknown_uuid")
    conv_created_at = conversation_data.get("created_at", "N/A")

    iso_date = "unknown-date"
    if conv_created_at != "N/A" and "T" in conv_created_at:
        iso_date = conv_created_at.split("T")[0]

    name_slug = create_slug(conv_name)
    short_uuid = conv_uuid.split("-")[0]  # Use first part of UUID for uniqueness

    md_filename = f"{iso_date}_{name_slug}_{short_uuid}.md"
    return md_filename


def generate_markdown_content(conversation_data: dict, conv_name: str) -> list[str]:
    """Generates the Markdown content for a single conversation."""
    conv_uuid = conversation_data.get("uuid", "unknown_uuid")
    conv_created_at = conversation_data.get("created_at", "N/A")
    conv_updated_at = conversation_data.get("updated_at", "N/A")
    chat_messages = conversation_data.get("chat_messages", [])

    md_content_lines = []
    md_content_lines.append(f"# Conversation: {conv_name}\n")
    md_content_lines.append(f"**UUID:** {conv_uuid}")
    md_content_lines.append(f"**Created At:** {conv_created_at}")
    md_content_lines.append(f"**Updated At:** {conv_updated_at}\n")
    md_content_lines.append("## Messages\n")

    for msg_idx, msg in enumerate(chat_messages):
        if not isinstance(msg, dict):
            logger.warning(
                f"Skipping malformed message at index {msg_idx} for conversation {conv_uuid} during MD generation."
            )
            continue

        md_content_lines.append("---")
        sender = msg.get("sender", "Unknown Sender")
        msg_created_at = msg.get("created_at", "N/A")

        msg_text_outer = msg.get("text", "")
        msg_text_inner = ""

        content_list = msg.get("content", [])
        if isinstance(content_list, list) and len(content_list) > 0:
            first_content_item = content_list[0]
            if isinstance(first_content_item, dict):
                msg_text_inner = first_content_item.get("text", "")

        msg_text_to_use = msg_text_inner if msg_text_inner else msg_text_outer

        md_content_lines.append(f"**Sender:** {sender.capitalize()}")
        md_content_lines.append(f"**Timestamp:** {msg_created_at}")

        files = msg.get("files", [])
        if files and isinstance(files, list):
            file_names = [
                f.get("file_name", "unknown_file")
                for f in files
                if isinstance(f, dict) and "file_name" in f
            ]
            if file_names:
                md_content_lines.append(f"**Attachments:** {', '.join(file_names)}")

        if msg_text_to_use:
            md_content_lines.append(f"\n{msg_text_to_use.strip()}\n")
        else:
            md_content_lines.append("\n\n")
    return md_content_lines


def write_markdown_file(
    filepath: Path, content_lines: list[str], conv_name: str, conv_uuid: str
) -> bool:
    """Writes the Markdown content to a file."""
    logger.debug(
        f"Preparing to write Markdown for '{conv_name}' (UUID: {conv_uuid}) to {filepath}"
    )
    try:
        with filepath.open("w", encoding="utf-8") as md_file:
            md_file.write("\n".join(content_lines))
        logger.debug(f"Successfully wrote: {filepath.name} (UUID: {conv_uuid})")
        return True
    except IOError as e:
        logger.error(f"Error writing Markdown file {filepath} (UUID: {conv_uuid}): {e}")
        return False
    except Exception as e:
        logger.exception(
            f"An unexpected error occurred while writing {filepath} (UUID: {conv_uuid}): {e}"
        )
        return False


def create_slug(text: str, max_length: int = 50) -> str:
    """Generates a URL-friendly slug from a string.

    The process involves:
    1. Converting the input text to lowercase.
    2. Replacing one or more whitespace characters with a single hyphen.
    3. Removing any characters that are not lowercase alphanumeric (a-z, 0-9) or a hyphen.
    4. Stripping any leading or trailing hyphens.
    5. Collapsing sequences of two or more hyphens into a single hyphen.
    6. Truncating the slug to `max_length`.
    7. Returning "untitled" if the original text is empty or if the slug becomes empty after processing.
    """
    if not text:  # Handle empty input string
        return "untitled"
    slug = text.lower()
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    slug = slug.strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    slug = slug[:max_length]
    slug = slug.strip("-")

    if not slug:
        return "untitled"
    return slug


def json_to_markdown(
    json_file_path: Path, output_dir: Path, limit: Optional[int] = None
):
    """
    Reads a JSON file containing a list of conversations, extracts relevant information,
    and writes each conversation to a separate Markdown file in the output directory.
    Can limit the number of conversations processed.
    """
    logger.info(
        f"Starting Markdown conversion process. Input: '{json_file_path}', Output dir: '{output_dir}', Limit: {limit}"
    )
    if not output_dir.exists():
        try:
            output_dir.mkdir(
                parents=True, exist_ok=True
            )  # parents=True to create parent dirs if needed, exist_ok=True to not raise error if it exists
            logger.info(f"Created output directory: {output_dir.resolve()}")
        except OSError as e:
            logger.exception(f"Error creating output directory {output_dir}: {e}")
            return

    conversations = load_and_validate_conversations(json_file_path)
    if conversations is None:
        return  # Errors already logged by the helper function

    original_total_conversations = len(conversations)
    logger.info(f"Found {original_total_conversations} conversations in the JSON file.")
    if limit is not None and limit >= 0:
        conversations_to_process = conversations[:limit]
        if limit == 0:
            logger.info("Processing limit is 0, no conversations will be processed.")
            return
        # This print is still useful to show context before progress bar starts
        logger.info(
            f"Processing {len(conversations_to_process)} of {original_total_conversations} total conversations (limit applied)."
        )
    else:
        conversations_to_process = conversations
        # logger.info(f"Processing all {len(conversations_to_process)} conversations.") # Already logged above

    if not conversations_to_process:
        logger.info("No conversations to process.")
        return

    processed_count = 0
    skipped_empty_name_count = 0
    skipped_no_content_count = 0
    failed_write_count = 0
    # Removed Progress wrapper
    for i, conv in enumerate(conversations_to_process):
        conv_uuid = conv.get("uuid", f"unknown_uuid_{i}")
        original_conv_name = conv.get("name")

        # Condition 1: Skip if conversation name is empty or None
        if not original_conv_name:
            logger.debug(
                f"Skipping conversation (UUID: {conv_uuid}) due to empty name."
            )
            skipped_empty_name_count += 1
            continue

        # Use the original name if present, otherwise default (though we just checked it's not empty)
        conv_name = original_conv_name  # Will be truthy here

        # Condition 2: Skip if all messages are empty or no messages exist
        chat_messages = conv.get("chat_messages", [])
        has_any_message_content = False
        if not chat_messages:  # No messages at all
            logger.warning(
                f"Skipping conversation '{conv_name}' (UUID: {conv_uuid}) due to no messages."
            )
            skipped_no_content_count += 1
            continue

        for msg_check in chat_messages:
            if not isinstance(msg_check, dict):
                logger.debug(
                    f"Malformed message object found during pre-check for conv {conv_uuid}. Skipping this message for content check."
                )
                continue  # Skip malformed message objects for content check
            msg_text_outer_check = msg_check.get("text", "")
            msg_text_inner_check = ""
            content_list_check = msg_check.get("content", [])
            if isinstance(content_list_check, list) and len(content_list_check) > 0:
                first_content_item_check = content_list_check[0]
                if isinstance(first_content_item_check, dict):
                    msg_text_inner_check = first_content_item_check.get("text", "")

            msg_text_to_use_check = (
                msg_text_inner_check if msg_text_inner_check else msg_text_outer_check
            )
            if msg_text_to_use_check and msg_text_to_use_check.strip():
                has_any_message_content = True
                break  # Found a message with content, no need to check further

        if not has_any_message_content:
            logger.warning(
                f"Skipping conversation '{conv_name}' (UUID: {conv_uuid}) because all messages are empty."
            )
            skipped_no_content_count += 1
            continue

        # Proceed with Markdown generation if checks passed
        # conv_created_at = conv.get('created_at', 'N/A') # Moved to generate_filename
        # conv_updated_at = conv.get('updated_at', 'N/A') # Will be used by generate_markdown_content

        md_filename = generate_filename(conv, conv_name)

        md_content_lines = generate_markdown_content(conv, conv_name)

        md_filepath = output_dir / md_filename

        # logger.debug(f"Preparing to write Markdown for '{conv_name}' (UUID: {conv_uuid}) to {md_filepath}") # Moved to write_markdown_file

        if write_markdown_file(md_filepath, md_content_lines, conv_name, conv_uuid):
            processed_count += 1
        else:
            failed_write_count += 1

    summary_msg = (
        f"Finished processing. Processed: {processed_count}. "
        f"Skipped (empty name): {skipped_empty_name_count}. "
        f"Skipped (no content): {skipped_no_content_count}. "
        f"Failed writes: {failed_write_count}."
    )
    logger.info(summary_msg)
