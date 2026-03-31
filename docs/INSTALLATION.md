# Installation & Setup

Claw Code has **no external dependencies** — it uses only the Python standard library. There is no `pip install` step.

---

## Prerequisites

- **Python 3.10 or later**

  The codebase uses union type syntax (`X | None`) in type annotations and `from __future__ import annotations` throughout. Python 3.9 and earlier are not supported.

  Check your version:

  ```bash
  python3 --version
  ```

---

## Clone the Repository

```bash
git clone https://github.com/instructkr/claw-code.git
cd claw-code
```

No virtual environment or dependency installation is needed.

---

## Verify the Installation

Render the porting workspace summary:

```bash
python3 -m src.main summary
```

Expected output begins with:

```
# Python Porting Workspace Summary

Port root: ...
Total Python files: ...

Command surface: 207 mirrored entries
...
```

Print the workspace manifest:

```bash
python3 -m src.main manifest
```

---

## Run the Tests

```bash
python3 -m unittest discover -s tests -v
```

All 20 tests should pass. The test suite covers:

- Manifest file counting
- CLI subcommand smoke tests (subprocess-based)
- Snapshot integrity (≥150 commands, ≥100 tools)
- Session persistence and reload
- Permission filtering
- Streaming event emission
- Bootstrap and turn-loop execution

---

## Platform Notes

The project runs on Linux, macOS, and Windows. All file I/O uses `pathlib.Path`, which handles platform path separators automatically.

Session files are written to `.port_sessions/` relative to the directory where you run the CLI. This directory is created automatically on first use.

---

## Optional: Local TypeScript Archive for Parity Auditing

If you have the original TypeScript source available locally, place it in an `archive/` directory at the repository root (this path is listed in `.gitignore` and will not be committed).

Then run:

```bash
python3 -m src.main parity-audit
```

This compares the Python workspace coverage against the archived surface. Without the local archive the command still runs and reports the JSON-snapshot-based coverage metrics.

---

## Rust Port (Upcoming)

A Rust port is in progress on the `dev/rust` branch. It aims to provide a faster, memory-safe harness runtime. Check that branch for the latest status.
