"""Tests for gemini_agent_sdk.events — parsing JSONL dicts into typed events."""

from gemini_agent_sdk.events import (
    ErrorEvent,
    InitEvent,
    MessageEvent,
    ResultEvent,
    ToolResultEvent,
    ToolUseEvent,
    parse_event,
)


def test_parse_init_event():
    data = {"type": "init", "session_id": "abc-123", "model": "gemini-2.5-pro"}
    event = parse_event(data)
    assert isinstance(event, InitEvent)
    assert event.session_id == "abc-123"
    assert event.model == "gemini-2.5-pro"


def test_parse_message_event():
    data = {"type": "message", "role": "assistant", "content": "Hello world"}
    event = parse_event(data)
    assert isinstance(event, MessageEvent)
    assert event.role == "assistant"
    assert event.content == "Hello world"


def test_parse_tool_use_event():
    data = {
        "type": "tool_use",
        "tool_name": "mcp_ghidra-mcp_read_file",
        "tool_id": "mcp_ghidra-mcp_read_file_1776315320245_0",
        "parameters": {"path": "/tmp/foo"},
    }
    event = parse_event(data)
    assert isinstance(event, ToolUseEvent)
    assert event.name == "mcp_ghidra-mcp_read_file"
    assert event.tool_id == "mcp_ghidra-mcp_read_file_1776315320245_0"
    assert event.arguments == {"path": "/tmp/foo"}


def test_parse_tool_result_event():
    data = {
        "type": "tool_result",
        "tool_id": "mcp_ghidra-mcp_read_file_1776315320245_0",
        "status": "success",
        "output": "file contents",
    }
    event = parse_event(data)
    assert isinstance(event, ToolResultEvent)
    assert event.name == "mcp_ghidra-mcp_read_file"
    assert event.tool_id == "mcp_ghidra-mcp_read_file_1776315320245_0"
    assert event.output == "file contents"
    assert event.is_error is False


def test_parse_tool_result_error():
    data = {
        "type": "tool_result",
        "tool_id": "mcp_ghidra-mcp_read_file_1776315320245_0",
        "status": "error",
        "output": "not found",
    }
    event = parse_event(data)
    assert isinstance(event, ToolResultEvent)
    assert event.is_error is True


def test_parse_error_event():
    data = {"type": "error", "message": "rate limit exceeded", "fatal": False}
    event = parse_event(data)
    assert isinstance(event, ErrorEvent)
    assert event.message == "rate limit exceeded"
    assert event.fatal is False


def test_parse_result_event():
    data = {
        "type": "result",
        "response": "Done.",
        "stats": {
            "total_tokens": 150,
            "input_tokens": 100,
            "output_tokens": 50,
            "cached": 80,
        },
    }
    event = parse_event(data)
    assert isinstance(event, ResultEvent)
    assert event.response == "Done."
    assert event.input_tokens == 100
    assert event.output_tokens == 50


def test_parse_unknown_type_returns_none():
    data = {"type": "unknown_future_event", "foo": "bar"}
    assert parse_event(data) is None


def test_parse_missing_type_returns_none():
    data = {"role": "assistant", "content": "no type field"}
    assert parse_event(data) is None


def test_parse_extra_fields_ignored():
    data = {"type": "init", "session_id": "s1", "model": "m1", "extra_field": True}
    event = parse_event(data)
    assert isinstance(event, InitEvent)
    assert event.session_id == "s1"


def test_parse_minimal_result():
    data = {"type": "result"}
    event = parse_event(data)
    assert isinstance(event, ResultEvent)
    assert event.response == ""
    assert event.input_tokens == 0
    assert event.output_tokens == 0
