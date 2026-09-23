# AI Agent Study

This project is for studying AI Agent.

## Overview

AIAgentStudy is a Python-based educational project that demonstrates a simple AI agent implementation. The agent uses OpenAI-compatible chat completions with tool calling capabilities to perform tasks like mathematical calculations and time retrieval.

## Project Structure

```
.
├── AGENTS.md                 # Agent contract and guidelines
├── README.md                 # This file
├── RUNBOOK.md                # Operational runbook
├── main.py                   # Root entry point
├── pyproject.toml            # Project configuration
├── 00.simple-agent/          # Simple agent implementation
│   ├── agent.py              # Agent runner with tool calling loop
│   ├── config.py             # Agent configuration
│   ├── tools.py              # Tool definitions (calculator, time)
│   ├── main.py               # Agent demo script
│   └── test.py               # Test script
└── prompt/
    └── execspec.md           # Agent execution specification
```

## Components

### 00.simple-agent

A minimal AI agent implementation featuring:

- **Tools**: `calculator` (evaluates mathematical expressions) and `get_current_time` (returns current ISO timestamp)
- **Agent Loop**: Chat completions with automatic tool calling via OpenAI API
- **Configuration**: Environment-driven settings (API base, model, API key)

### Root

- `main.py`: Simple hello-world entry point
- `pyproject.toml`: Project metadata and dependencies (OpenAI SDK)

## Getting Started

1. Install dependencies:
   ```bash
   pip install -e .
   ```

2. Run the agent demo:
   ```bash
   python 00.simple-agent/main.py
   ```

3. Run tests:
   ```bash
   python 00.simple-agent/test.py
   ```

## Configuration

The agent is configured via `00.simple-agent/config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `api_base` | `http://gx10:8000/v1` | OpenAI-compatible API endpoint |
| `api_key` | `dummy` | API key (replace with real key) |
| `model` | `gpt-oss-120b` | Model to use |
| `tools` | `TOOL_SCHEMAS` | Tool schema reference |

> **Note**: The `api_key` is set to `dummy` for demonstration. Replace with a valid key for production use.

## License

MIT