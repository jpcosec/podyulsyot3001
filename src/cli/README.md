# CLI Module

Unified operator CLI for Postulator 3000.

---

## 🏗️ Architecture & Features

The CLI serves as the single entry point for all operator-facing commands. Commands are organized into a modular structure where each command lives in its own file under `commands/`.

- Entry point: `src/cli/main.py`
- Command handlers: `src/cli/commands/`
- Shared utilities: `src/cli/commands/_utils.py`

---

## ⚙️ Configuration

Required environment variables:

- `GOOGLE_API_KEY` — Gemini API key for LLM calls
- `GEMINI_API_KEY` — Alternative Gemini API key
- `LOG_DIR` — Directory for log files (optional)

---

## 🚀 CLI / UI / Usage

Run the CLI via Python module:

```bash
python -m src.cli.main <command> [options]
```

Arguments are defined in the parser builders within each command module. Run `--help` on any command for details.

---

## 📝 Data Contract

The CLI does not define data contracts — it orchestrates calls to core modules that do. Key entry points:

- Pipeline execution: `src/core/ai/generate_documents_v2/`
- Translation: `src/core/tools/translator/`
- Rendering: `src/core/tools/render/`

---

## 🛠️ How to Add / Extend

1. Create a new file in `src/cli/commands/` (e.g., `newcmd.py`)
2. Define `add_parser(subparsers)` to register the subcommand
3. Define `run(args) -> int` to implement the command logic
4. Import and add to `COMMAND_HANDLERS` in `src/cli/commands/__init__.py`
5. Import the `add_parser` function in `src/cli/main.py` and call it in `_build_parser()`
6. Add tests in `tests/unit/cli/`

---

## 💻 How to Use

```bash
# Start LangGraph API server
python -m src.cli.main api start

# Run full pipeline
python -m src.cli.main pipeline --source xing --job-id 123

# Batch run
python -m src.cli.main run-batch --sources xing stepstone --limit 5

# Launch review UI
python -m src.cli.main review

# Run demo
python -m src.cli.main demo
```

---

## 🚑 Troubleshooting

**LangGraph API not reachable**
Start the API server first: `python -m src.cli.main api start`

**Review UI fails to connect**
Ensure the API server is running and the thread exists for the specified job.
