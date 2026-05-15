"""Tests for gemini_cli_sdk.client — GeminiCli, options, and streaming."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gemini_cli_sdk.client import GeminiCli, GeminiOptions, SyncResult
from gemini_cli_sdk.events import (
    InitEvent,
    MessageEvent,
    ResultEvent,
    ToolUseEvent,
    ToolResultEvent,
)


def test_options_defaults():
    opts = GeminiOptions()
    assert opts.model == "gemini-2.5-pro"
    assert opts.approval_mode == "yolo"
    assert opts.allowed_mcp_servers == []
    assert opts.timeout == 600.0


def test_build_args():
    opts = GeminiOptions(
        model="gemini-2.5-flash",
        approval_mode="auto_edit",
        allowed_mcp_servers=["ghidra-mcp"],
    )
    with patch(
        "gemini_cli_sdk.client.find_gemini_binary", return_value="/usr/bin/gemini"
    ):
        cli = GeminiCli(opts)

    args = cli._build_args("Hello world")
    assert "/usr/bin/gemini" in args
    assert "--output-format" in args
    assert "stream-json" in args
    assert "--approval-mode" in args
    assert "auto_edit" in args
    assert "--model" in args
    assert "gemini-2.5-flash" in args
    assert "--allowed-mcp-server-names" in args
    assert "ghidra-mcp" in args
    assert "-p" in args
    # Prompt is now sent via stdin, so -p is empty string
    idx = args.index("-p")
    assert args[idx + 1] == ""


@pytest.mark.asyncio
async def test_run_streams_events():
    """Test that run() yields parsed events from JSONL stdout."""
    jsonl_lines = [
        json.dumps({"type": "init", "session_id": "s1", "model": "gemini-2.5-pro"}),
        json.dumps({"type": "message", "role": "assistant", "content": "Hi"}),
        json.dumps(
            {"type": "tool_use", "name": "read_file", "arguments": {"path": "x"}}
        ),
        json.dumps(
            {
                "type": "tool_result",
                "name": "read_file",
                "output": "data",
                "is_error": False,
            }
        ),
        json.dumps(
            {
                "type": "result",
                "response": "Done",
                "input_tokens": 10,
                "output_tokens": 5,
            }
        ),
    ]
    stdout_data = ("\n".join(jsonl_lines) + "\n").encode()

    mock_stdin = MagicMock()
    mock_stdin.write = MagicMock()
    mock_stdin.close = MagicMock()

    mock_process = AsyncMock()
    mock_process.stdin = mock_stdin
    mock_process.stdout = AsyncMock()
    mock_process.stderr = AsyncMock()
    mock_process.returncode = 0

    # Simulate reading: first call returns all data, second returns empty
    read_calls = [stdout_data, b""]
    mock_process.stdout.read = AsyncMock(side_effect=read_calls)
    mock_process.wait = AsyncMock(return_value=0)

    with patch(
        "gemini_cli_sdk.client.find_gemini_binary", return_value="/usr/bin/gemini"
    ):
        cli = GeminiCli(GeminiOptions())

    with patch("asyncio.create_subprocess_exec", return_value=mock_process):
        events = []
        async for event in cli.run("test prompt"):
            events.append(event)

    # Verify prompt was sent via stdin
    mock_stdin.write.assert_called_with(b"test prompt")
    mock_stdin.close.assert_called()

    assert len(events) == 5
    assert isinstance(events[0], InitEvent)
    assert isinstance(events[1], MessageEvent)
    assert isinstance(events[2], ToolUseEvent)
    assert isinstance(events[3], ToolResultEvent)
    assert isinstance(events[4], ResultEvent)
    assert events[4].response == "Done"
    assert events[4].input_tokens == 10


@pytest.mark.asyncio
async def test_run_sync_returns_result():
    """Test that run_sync() returns a SyncResult."""
    jsonl_lines = [
        json.dumps({"type": "init", "session_id": "s1", "model": "m1"}),
        json.dumps(
            {
                "type": "result",
                "response": "Answer",
                "input_tokens": 50,
                "output_tokens": 20,
            }
        ),
    ]
    stdout_data = ("\n".join(jsonl_lines) + "\n").encode()

    mock_stdin = MagicMock()
    mock_stdin.write = MagicMock()
    mock_stdin.close = MagicMock()

    mock_process = AsyncMock()
    mock_process.stdin = mock_stdin
    mock_process.stdout = AsyncMock()
    mock_process.stderr = AsyncMock()
    mock_process.returncode = 0
    mock_process.stdout.read = AsyncMock(side_effect=[stdout_data, b""])
    mock_process.wait = AsyncMock(return_value=0)

    with patch(
        "gemini_cli_sdk.client.find_gemini_binary", return_value="/usr/bin/gemini"
    ):
        cli = GeminiCli(GeminiOptions())

    with patch("asyncio.create_subprocess_exec", return_value=mock_process):
        result = await cli.run_sync("test")

    assert isinstance(result, SyncResult)
    assert result.response == "Answer"
    assert result.input_tokens == 50
    assert result.output_tokens == 20
    assert len(result.events) == 2
