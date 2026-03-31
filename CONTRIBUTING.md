# Contributing to Claw Code

Thank you for your interest in contributing. This document explains how to get involved.

---

## Code of Conduct

Be respectful. Harassment, discrimination, or abusive behaviour in any project space will not be tolerated.

---

## Reporting Issues

Open an issue on GitHub describing:

1. What you expected to happen
2. What actually happened
3. The full command you ran and its output
4. Your Python version (`python3 --version`) and operating system

---

## Development Setup

```bash
git clone https://github.com/instructkr/claw-code.git
cd claw-code
python3 -m unittest discover -s tests -v   # all 20 tests should pass
```

No virtual environment or extra dependencies are needed.

---

## Branch Naming

| Branch prefix | Purpose |
|---------------|---------|
| `feat/<short-description>` | New feature or subsystem port |
| `fix/<short-description>` | Bug fix |
| `docs/<short-description>` | Documentation only |
| `refactor/<short-description>` | Internal restructuring, no behaviour change |
| `dev/rust` | Rust port (maintained separately) |

Target PRs at `main`.

---

## Pull Request Workflow

1. Fork the repository and create a branch from `main`.
2. Make your changes.
3. Run the full test suite — all tests must pass:
   ```bash
   python3 -m unittest discover -s tests -v
   ```
4. Open a PR with a clear title and a description of what changed and why.

---

## Code Style Expectations

- **`from __future__ import annotations`** at the top of every module.
- **Type hints** on all function signatures and dataclass fields.
- **Frozen dataclasses** for all value objects (`@dataclass(frozen=True)`).
- **`functools.lru_cache`** for functions that load JSON snapshots (avoid re-reading files on every call).
- **No external dependencies.** The project uses only the Python standard library. Do not add `pip` dependencies.
- Keep modules focused. If a new concept needs its own module, add a new file rather than growing an existing one.

---

## Adding a Subsystem Package

Each of the 30 subsystem packages in `src/` follows the same pattern. To add a new one:

1. Create `src/<name>/__init__.py` that loads from `src/reference_data/subsystems/<name>.json`.
2. Add a corresponding JSON file in `src/reference_data/subsystems/` with keys: `archive_name`, `module_count`, `sample_files`, `porting_note`.
3. Add a test in `tests/test_porting_workspace.py` asserting `MODULE_COUNT > 0`.

---

## Adding Commands or Tools to the Inventory

The command and tool inventories are driven by:

- `src/reference_data/commands_snapshot.json`
- `src/reference_data/tools_snapshot.json`

Each entry has the shape:

```json
{
  "name": "ExampleCommand",
  "source_hint": "src/commands/example.ts",
  "responsibility": "One-sentence description of what this command does."
}
```

After editing a snapshot, run the full test suite to verify the minimum entry counts still pass (`≥150` commands, `≥100` tools).

---

## Test Requirements

Every PR must keep all existing tests passing. New behaviour should be covered by new tests. The testing patterns used in `tests/test_porting_workspace.py` are:

- **Unit**: import and call Python API directly.
- **CLI integration**: use `subprocess.run([sys.executable, '-m', 'src.main', ...])` and assert on stdout.

---

## Commit Message Format

```
<type>: <short summary in present tense>

[Optional longer description]
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`.

Example:

```
feat: add transcript compaction to QueryEnginePort
```

---

## Legal: Clean-Room Policy

This project is a clean-room rewrite. Contributions must not:

- Copy or closely paraphrase any portion of the original Claude Code TypeScript source.
- Include any Anthropic proprietary material.

By submitting a PR you confirm that your contribution is your original work and is free of third-party proprietary content.
