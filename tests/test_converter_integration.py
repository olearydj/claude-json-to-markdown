import subprocess
import tempfile
import shutil
import json
from pathlib import Path
import os
import pytest

# Path to the script to be tested
PROJECT_ROOT = Path(__file__).parent.parent
SCRIPT_PATH = PROJECT_ROOT / "claude_json2md" / "cli.py"


@pytest.fixture
def temp_test_env():
    """Set up a temporary directory for test outputs and inputs and yield paths."""
    test_dir = tempfile.mkdtemp(prefix="converter_pytest_")
    output_dir = Path(test_dir) / "output"
    input_file_path = Path(test_dir) / "sample_input.json"

    # Yield a dictionary or an object containing these paths
    yield {
        "test_dir": Path(test_dir),
        "output_dir": output_dir,
        "input_file_path": input_file_path,
    }

    # Teardown: Clean up the temporary directory
    shutil.rmtree(test_dir)


def create_sample_json(file_path, conversations_data):
    """Helper to create a sample JSON input file."""
    with open(file_path, "w") as f:
        json.dump(conversations_data, f)


def run_script_command(input_file, output_dir, limit=None):
    env = os.environ.copy()
    # PYTHONPATH manipulation is likely not needed anymore if cj2md is correctly installed in the venv

    cmd = [
        "cj2md",  # Use the installed script/entry point
        str(input_file),
        str(output_dir),
    ]
    if limit is not None:
        cmd.extend(["--limit", str(limit)])

    return subprocess.run(cmd, capture_output=True, text=True, check=False, env=env)


def test_basic_conversion_and_skip(temp_test_env):
    """Test basic conversion and skipping logic."""
    input_file = temp_test_env["input_file_path"]
    output_dir = temp_test_env["output_dir"]

    sample_data = [
        {
            "uuid": "valid-uuid-123",
            "name": "Valid Test Conversation",
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-01T11:00:00Z",
            "chat_messages": [
                {
                    "uuid": "msg-uuid-1",
                    "text": "Hello from human",
                    "sender": "human",
                    "created_at": "2024-01-01T10:01:00Z",
                },
                {
                    "uuid": "msg-uuid-2",
                    "text": "Hello from assistant",
                    "sender": "assistant",
                    "created_at": "2024-01-01T10:02:00Z",
                },
            ],
        },
        {
            "uuid": "empty-name-uuid-456",
            "name": "",
            "created_at": "2024-01-02T12:00:00Z",
            "updated_at": "2024-01-02T13:00:00Z",
            "chat_messages": [
                {
                    "uuid": "msg-uuid-3",
                    "text": "This message won't appear",
                    "sender": "human",
                    "created_at": "2024-01-02T12:01:00Z",
                }
            ],
        },
        {
            "uuid": "no-messages-uuid-789",
            "name": "Conversation With No Messages",
            "created_at": "2024-01-03T14:00:00Z",
            "updated_at": "2024-01-03T15:00:00Z",
            "chat_messages": [],
        },
        {
            "uuid": "empty-messages-uuid-abc",
            "name": "Conversation With Empty Messages",
            "created_at": "2024-01-04T16:00:00Z",
            "updated_at": "2024-01-04T17:00:00Z",
            "chat_messages": [
                {
                    "uuid": "msg-uuid-4",
                    "text": "   ",
                    "sender": "human",
                    "created_at": "2024-01-04T16:01:00Z",
                }
            ],
        },
    ]
    create_sample_json(input_file, sample_data)

    result = run_script_command(input_file, output_dir)

    assert result.returncode == 0, f"Script failed with error: {result.stderr}"
    assert output_dir.exists(), "Output directory was not created."

    output_files = list(output_dir.glob("*.md"))
    assert len(output_files) == 1, (
        f"Expected 1 MD file, found {len(output_files)}. Files: {output_files}. Stderr: {result.stderr}"
    )

    if output_files:
        generated_file_name = output_files[0].name
        assert generated_file_name.startswith("2024-01-01_valid-test-conversation_"), (
            f"Filename {generated_file_name} does not start correctly."
        )
        assert generated_file_name.endswith("_valid.md"), (
            f"Filename {generated_file_name} does not end with _valid.md"
        )

        with open(output_files[0], "r") as f_md:
            content = f_md.read()
        assert "# Conversation: Valid Test Conversation" in content
        assert "Hello from human" in content
        assert "Hello from assistant" in content


def test_limit_argument(temp_test_env):
    """Test the --limit argument."""
    input_file = temp_test_env["input_file_path"]
    output_dir = temp_test_env["output_dir"]

    sample_data = [
        {
            "uuid": f"uuid-{i}",
            "name": f"Test Conversation {i}",
            "created_at": f"2024-01-01T10:0{i}:00Z",
            "updated_at": f"2024-01-01T11:0{i}:00Z",
            "chat_messages": [
                {
                    "uuid": f"msg-{i}-1",
                    "text": f"Msg {i}",
                    "sender": "human",
                    "created_at": f"2024-01-01T10:0{i}:01Z",
                }
            ],
        }
        for i in range(5)
    ]
    create_sample_json(input_file, sample_data)

    result = run_script_command(input_file, output_dir, limit=2)

    assert result.returncode == 0, f"Script failed with limit argument: {result.stderr}"
    output_files = list(output_dir.glob("*.md"))
    assert len(output_files) == 2, (
        f"Expected 2 MD files with limit=2, found {len(output_files)}."
    )


# No longer need: if __name__ == '__main__': unittest.main()
