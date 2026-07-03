# Tools

This folder contains helper tools for repeatable model tests against a locally hosted, OpenAI-compatible LLM server.

## Contents

- `llama_batch_test.py`
  - Runs multiple consecutive test iterations against `/v1/chat/completions`.
  - Uses raw TCP sockets for robust HTTP communication without keep-alive hangs.
  - Captures response text, tool calls, runtime, finish reason, and errors per run.
  - Useful for comparing model stability and behavior across many repetitions.

- `batch_results.json`
  - Example result file with logged responses from batch runs.
  - Used to evaluate consistency, error rates, and response quality across runs.

## What The Tools Are Used For

The tools are used to:

- test model latency and response behavior under repeated load,
- make tool-use behavior and stop reasons (`finish_reason`) transparent,
- store results reproducibly for later analysis.

## Quick Note

Before running the script, adjust the `CONFIG` section (server URL, model, prompt, number of repetitions, and timeouts).

## Mini Example: Execution

Run from the project root:

```bash
python3 tools/llama_batch_test.py
```

Typical output:

- One JSON line is written per test run.
- The output file is defined by `OUTPUT_FILE` in the script (default: `batch_results.jsonl`).
- Important fields per run include `run`, `timestamp`, `model`, `response`, `tool_calls`, `finish_reason`, `elapsed_s`, `error`.
