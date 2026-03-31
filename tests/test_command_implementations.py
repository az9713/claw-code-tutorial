from __future__ import annotations

import unittest

from src import stores
from src.command_implementations.core_commands import (
    handle_clear,
    handle_compact,
    handle_help,
    handle_status,
    handle_version,
)
from src.command_implementations.config_commands import (
    handle_config_command,
    handle_permissions,
    handle_skills,
    handle_tasks,
)
from src.command_implementations.session_commands import (
    handle_doctor,
    handle_memory,
    handle_model,
)


def _reset_stores() -> None:
    stores._tasks.clear()
    stores._teams.clear()
    stores._agents.clear()
    stores._todos.clear()
    stores._crons.clear()
    stores._config.clear()
    stores._mode_flags.clear()
    stores._mode_flags["plan_mode"] = False
    stores._mode_flags["worktree_mode"] = False


class TestHelpCommand(unittest.TestCase):
    def test_help_returns_text(self) -> None:
        result = handle_help("")
        self.assertGreater(len(result), 0)

    def test_help_contains_help_keyword(self) -> None:
        result = handle_help("")
        self.assertIn("help", result.lower())

    def test_help_with_known_command(self) -> None:
        result = handle_help("version")
        self.assertIn("version", result.lower())

    def test_help_with_unknown_command(self) -> None:
        result = handle_help("zzz_nonexistent_command")
        self.assertIn("No command found", result)


class TestVersionCommand(unittest.TestCase):
    def test_version_returns_python_version(self) -> None:
        result = handle_version("")
        self.assertIn("Python", result)

    def test_version_contains_platform(self) -> None:
        result = handle_version("")
        self.assertIn("Platform", result)

    def test_version_contains_claw_code(self) -> None:
        result = handle_version("")
        self.assertIn("claw-code", result)


class TestClearAndCompact(unittest.TestCase):
    def test_clear_returns_message(self) -> None:
        result = handle_clear("")
        self.assertIn("cleared", result.lower())

    def test_compact_returns_message(self) -> None:
        result = handle_compact("")
        self.assertIn("compacted", result.lower())


class TestStatusCommand(unittest.TestCase):
    def setUp(self) -> None:
        _reset_stores()

    def test_status_returns_platform(self) -> None:
        result = handle_status("")
        self.assertTrue(
            "Platform" in result or "Python" in result,
            f"Expected 'Platform' or 'Python' in: {result!r}",
        )

    def test_status_shows_task_count(self) -> None:
        result = handle_status("")
        self.assertIn("Active tasks", result)

    def test_status_shows_mode_flags(self) -> None:
        result = handle_status("")
        self.assertIn("Plan mode", result)


class TestModelCommand(unittest.TestCase):
    def setUp(self) -> None:
        _reset_stores()

    def test_model_returns_model_name(self) -> None:
        result = handle_model("")
        self.assertTrue(
            "claude" in result.lower() or "model" in result.lower(),
            f"Expected 'claude' or 'model' in: {result!r}",
        )


class TestMemoryCommand(unittest.TestCase):
    def test_memory_no_file_returns_informative_message(self) -> None:
        # Running from a directory without CLAUDE.md several levels up is not
        # guaranteed; we just ensure the result is a non-empty string that
        # either reports the file location or indicates it was not found.
        result = handle_memory("")
        self.assertGreater(len(result), 0)
        # Should mention CLAUDE.md either way
        self.assertIn("CLAUDE.md", result)


class TestDoctorCommand(unittest.TestCase):
    def test_doctor_passes(self) -> None:
        result = handle_doctor("")
        self.assertGreater(len(result), 0)
        # Should mention PASS or OK somewhere in the output
        result_lower = result.lower()
        self.assertTrue(
            "pass" in result_lower or "ok" in result_lower,
            f"Expected 'pass' or 'ok' in doctor output: {result!r}",
        )


class TestSkillsCommand(unittest.TestCase):
    def test_skills_returns_list_or_empty_message(self) -> None:
        result = handle_skills("")
        self.assertGreater(len(result), 0)
        self.assertTrue(
            "skill" in result.lower() or "No skills" in result,
            f"Expected skills listing or 'No skills' in: {result!r}",
        )


class TestTasksCommand(unittest.TestCase):
    def setUp(self) -> None:
        _reset_stores()

    def test_tasks_empty(self) -> None:
        result = handle_tasks("")
        self.assertTrue(
            "No tasks" in result or result.strip() == "[]",
            f"Expected 'No tasks' or '[]' when no tasks exist, got: {result!r}",
        )

    def test_tasks_after_creating_one(self) -> None:
        stores.create_task("demo task", "for testing")
        result = handle_tasks("")
        self.assertIn("demo task", result)


class TestPermissionsCommand(unittest.TestCase):
    def test_permissions_info(self) -> None:
        result = handle_permissions("")
        self.assertGreater(len(result), 0)
        # Should mention permission model or ToolPermissionContext
        result_lower = result.lower()
        self.assertTrue(
            "permission" in result_lower or "toolpermissioncontext" in result_lower,
            f"Expected permission info in: {result!r}",
        )


class TestConfigCommandRoundtrip(unittest.TestCase):
    def setUp(self) -> None:
        _reset_stores()

    def test_config_set_via_command(self) -> None:
        handle_config_command("mykey=myval")
        result = handle_config_command("mykey")
        self.assertIn("myval", result)

    def test_config_set_with_spaces(self) -> None:
        handle_config_command("theme = dark")
        result = handle_config_command("theme")
        self.assertIn("dark", result)

    def test_config_list_empty(self) -> None:
        result = handle_config_command("")
        # Should return JSON or empty dict representation
        self.assertIsNotNone(result)

    def test_config_get_after_multiple_sets(self) -> None:
        handle_config_command("key1=val1")
        handle_config_command("key2=val2")
        self.assertIn("val1", handle_config_command("key1"))
        self.assertIn("val2", handle_config_command("key2"))


if __name__ == "__main__":
    unittest.main()
