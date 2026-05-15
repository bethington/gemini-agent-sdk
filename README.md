# gemini-agent-sdk

An **agentic harness** for Google's Gemini CLI — drive Gemini as a
tool-using agent from Python: native `stream-json` parsing, a full
tool-call event stream, MCP-server wiring, and approval modes.

This SDK wraps the `gemini` binary (from [`@google/gemini-cli`](https://www.npmjs.com/package/@google/gemini-cli)). It spawns the CLI in headless mode and streams typed JSONL events over stdout.

> **Not the same as `gemini-cli-sdk`.** The PyPI package `gemini-cli-sdk`
> ([`oneryalcin/gemini-cli-sdk`](https://github.com/oneryalcin/gemini-cli-sdk))
> is an unrelated project — a Claude-Code-SDK-compatible chat wrapper
> (`query()` + Pydantic models, LLM-based output parsing). This SDK is a
> different shape: a class-based agent runner with native JSON parsing and
> per-tool-call event objects, built for workloads where Gemini calls MCP
> tools in a loop. The two were briefly name-collided; this package was
> renamed `gemini-cli-sdk` → `gemini-agent-sdk` (import `gemini_cli_sdk`
> → `gemini_agent_sdk`) so both can be installed side-by-side. See
> [bethington/ghidra-mcp#201](https://github.com/bethington/ghidra-mcp/issues/201)
> for the full story.

## Installation

```bash
pip install git+https://github.com/bethington/gemini-agent-sdk@main
```

If your environment can't git-clone over HTTPS, the tarball install works too:

```bash
pip install https://github.com/bethington/gemini-agent-sdk/archive/refs/heads/main.tar.gz
```

Requires Python 3.10+ and the Gemini CLI binary installed:

```bash
npm install -g @google/gemini-cli
```

## Quickstart

```python
import asyncio
from gemini_agent_sdk import GeminiCli, GeminiOptions

async def main():
    cli = GeminiCli(GeminiOptions(model="gemini-2.5-flash"))

    # Streaming mode
    async for event in cli.run("Explain this codebase"):
        print(event)

    # Or get just the final result
    result = await cli.run_sync("Summarize README.md")
    print(result.response)

asyncio.run(main())
```

## Streaming Events

The `run()` method yields typed event objects:

| Event | Fields | Description |
|-------|--------|-------------|
| `InitEvent` | `session_id`, `model` | Session metadata |
| `MessageEvent` | `role`, `content` | User/assistant messages |
| `ToolUseEvent` | `name`, `arguments` | Tool call request |
| `ToolResultEvent` | `name`, `output`, `is_error` | Tool execution result |
| `ErrorEvent` | `message`, `fatal` | Warnings and errors |
| `ResultEvent` | `response`, `input_tokens`, `output_tokens` | Final result with stats |

## Options

```python
GeminiOptions(
    model="gemini-2.5-pro",          # Model name or alias
    approval_mode="yolo",            # "default" | "auto_edit" | "yolo" | "plan"
    allowed_mcp_servers=["my-mcp"],  # MCP server names to enable
    cwd="/path/to/project",          # Working directory
    env={"API_KEY": "..."},          # Extra environment variables
    timeout=600.0,                   # Process timeout in seconds
    gemini_path="/path/to/gemini",   # Override binary path
)
```

## MCP Server Integration

Configure MCP servers in `~/.gemini/settings.json` or `.gemini/settings.json`:

```json
{
  "mcpServers": {
    "my-tools": {
      "command": "python",
      "args": ["-m", "my_mcp_server"],
      "trust": true
    }
  }
}
```

Then allow the server in your SDK options:

```python
cli = GeminiCli(GeminiOptions(allowed_mcp_servers=["my-tools"]))
```

## License

Apache 2.0
