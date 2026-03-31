from __future__ import annotations

import json
import os
import tempfile
import unittest

from src import stores
from src.tool_implementations.bash_tool import handle_bash_tool
from src.tool_implementations.config_tool import handle_config
from src.tool_implementations.file_edit_tool import handle_file_edit
from src.tool_implementations.file_read_tool import handle_file_read
from src.tool_implementations.file_write_tool import handle_file_write
from src.tool_implementations.glob_tool import handle_glob
from src.tool_implementations.grep_tool import handle_grep
from src.tool_implementations.mode_tools import handle_enter_plan_mode, handle_exit_plan_mode
from src.tool_implementations.agent_tools import handle_spawn_multi_agent
from src.tool_implementations.task_tools import (
    handle_task_create,
    handle_task_get,
    handle_task_list,
    handle_task_output,
    handle_task_stop,
    handle_task_update,
)
from src.tool_implementations.team_tools import handle_team_create, handle_team_delete
from src.tool_implementations.todo_tool import handle_todo_write
from src.tool_implementations.tool_search_tool import handle_tool_search
from src.tool_implementations.web_tools import handle_web_fetch


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


class TestFileReadTool(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def _make_file(self, name: str, content: str) -> str:
        path = os.path.join(self.tmpdir.name, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        return path

    def test_file_read_basic(self) -> None:
        path = self._make_file("hello.txt", "line one\nline two\nline three\n")
        result = handle_file_read(json.dumps({"file_path": path}))
        self.assertIn("1\t", result)
        self.assertIn("line one", result)
        self.assertIn("line two", result)
        self.assertIn("line three", result)

    def test_file_read_offset_limit(self) -> None:
        lines = "\n".join(f"line {i}" for i in range(1, 11))
        path = self._make_file("numbered.txt", lines)
        result = handle_file_read(json.dumps({"file_path": path, "offset": 2, "limit": 3}))
        # Lines 3-5 (0-indexed offset 2, limit 3)
        self.assertIn("line 3", result)
        self.assertIn("line 4", result)
        self.assertIn("line 5", result)
        self.assertNotIn("line 1", result)
        self.assertNotIn("line 6", result)

    def test_file_read_not_found(self) -> None:
        result = handle_file_read(json.dumps({"file_path": "/nonexistent/path/file.txt"}))
        self.assertIn("Error", result)

    def test_file_read_missing_path(self) -> None:
        result = handle_file_read("{}")
        self.assertIn("Error", result)


class TestFileWriteTool(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def test_file_write(self) -> None:
        path = os.path.join(self.tmpdir.name, "output.txt")
        result = handle_file_write(json.dumps({"file_path": path, "content": "hello world"}))
        self.assertIn("File written", result)
        self.assertTrue(os.path.isfile(path))
        with open(path, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "hello world")

    def test_file_write_creates_parent_dirs(self) -> None:
        path = os.path.join(self.tmpdir.name, "subdir", "nested", "file.txt")
        result = handle_file_write(json.dumps({"file_path": path, "content": "nested"}))
        self.assertIn("File written", result)
        self.assertTrue(os.path.isfile(path))

    def test_file_write_missing_path(self) -> None:
        result = handle_file_write("{}")
        self.assertIn("Error", result)


class TestFileEditTool(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def _make_file(self, name: str, content: str) -> str:
        path = os.path.join(self.tmpdir.name, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        return path

    def test_file_edit_success(self) -> None:
        path = self._make_file("edit_me.txt", "Hello world\nSecond line\n")
        result = handle_file_edit(json.dumps({
            "file_path": path,
            "old_string": "Hello world",
            "new_string": "Goodbye world",
        }))
        self.assertIn("Edited", result)
        with open(path, encoding="utf-8") as fh:
            content = fh.read()
        self.assertIn("Goodbye world", content)
        self.assertNotIn("Hello world", content)

    def test_file_edit_not_unique(self) -> None:
        path = self._make_file("dupe.txt", "foo bar foo")
        result = handle_file_edit(json.dumps({
            "file_path": path,
            "old_string": "foo",
            "new_string": "baz",
        }))
        self.assertIn("Error", result)

    def test_file_edit_old_string_missing(self) -> None:
        path = self._make_file("miss.txt", "content here")
        result = handle_file_edit(json.dumps({
            "file_path": path,
            "old_string": "DOES_NOT_EXIST",
            "new_string": "replacement",
        }))
        self.assertIn("Error", result)

    def test_file_edit_replace_all(self) -> None:
        path = self._make_file("multi.txt", "foo bar foo")
        result = handle_file_edit(json.dumps({
            "file_path": path,
            "old_string": "foo",
            "new_string": "baz",
            "replace_all": True,
        }))
        self.assertIn("Edited", result)
        with open(path, encoding="utf-8") as fh:
            content = fh.read()
        self.assertNotIn("foo", content)


class TestGlobTool(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def _make_file(self, name: str) -> None:
        path = os.path.join(self.tmpdir.name, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("# placeholder\n")

    def test_glob_basic(self) -> None:
        self._make_file("alpha.py")
        self._make_file("beta.py")
        self._make_file("gamma.txt")
        result = handle_glob(json.dumps({"pattern": "*.py", "path": self.tmpdir.name}))
        self.assertIn("alpha.py", result)
        self.assertIn("beta.py", result)
        self.assertNotIn("gamma.txt", result)

    def test_glob_no_matches(self) -> None:
        result = handle_glob(json.dumps({"pattern": "*.nonexistent", "path": self.tmpdir.name}))
        self.assertEqual(result.strip(), "")

    def test_glob_bad_path(self) -> None:
        result = handle_glob(json.dumps({"pattern": "*.py", "path": "/nonexistent/dir"}))
        self.assertIn("Error", result)


class TestGrepTool(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def _make_file(self, name: str, content: str) -> str:
        path = os.path.join(self.tmpdir.name, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        return path

    def test_grep_files_with_matches(self) -> None:
        self._make_file("match.txt", "the quick brown fox\njumps over\n")
        self._make_file("nomatch.txt", "nothing relevant here\n")
        result = handle_grep(json.dumps({
            "pattern": "quick",
            "path": self.tmpdir.name,
            "output_mode": "files_with_matches",
        }))
        self.assertIn("match.txt", result)
        self.assertNotIn("nomatch.txt", result)

    def test_grep_content(self) -> None:
        self._make_file("source.py", "def hello():\n    return 'world'\n")
        result = handle_grep(json.dumps({
            "pattern": "def hello",
            "path": self.tmpdir.name,
            "output_mode": "content",
        }))
        self.assertIn("def hello", result)

    def test_grep_missing_pattern(self) -> None:
        result = handle_grep(json.dumps({"path": self.tmpdir.name}))
        self.assertIn("Error", result)

    def test_grep_bad_regex(self) -> None:
        result = handle_grep(json.dumps({"pattern": "[invalid", "path": self.tmpdir.name}))
        self.assertIn("Error", result)


class TestBashTool(unittest.TestCase):
    def test_bash_echo(self) -> None:
        result = handle_bash_tool('{"command": "echo hello"}')
        self.assertIn("hello", result)

    def test_bash_security_block(self) -> None:
        result = handle_bash_tool('{"command": "rm -rf /"}')
        self.assertIn("Error", result)
        self.assertIn("blocked", result.lower())

    def test_bash_missing_command(self) -> None:
        result = handle_bash_tool("{}")
        self.assertIn("Error", result)

    def test_bash_empty_payload(self) -> None:
        result = handle_bash_tool("")
        self.assertIn("Error", result)

    def test_bash_multiline_output(self) -> None:
        result = handle_bash_tool('{"command": "echo line1 && echo line2"}')
        self.assertIn("line1", result)
        self.assertIn("line2", result)


class TestTaskTools(unittest.TestCase):
    def setUp(self) -> None:
        _reset_stores()

    def test_task_create_and_get(self) -> None:
        created_str = handle_task_create('{"name": "my task", "description": "do something"}')
        created = json.loads(created_str)
        self.assertEqual(created["name"], "my task")
        self.assertEqual(created["description"], "do something")
        self.assertEqual(created["status"], "pending")
        task_id = created["task_id"]

        fetched_str = handle_task_get(json.dumps({"task_id": task_id}))
        fetched = json.loads(fetched_str)
        self.assertEqual(fetched["task_id"], task_id)
        self.assertEqual(fetched["name"], "my task")

    def test_task_lifecycle(self) -> None:
        # Create
        created_str = handle_task_create('{"name": "lifecycle", "description": "test"}')
        created = json.loads(created_str)
        task_id = created["task_id"]

        # Update status
        updated_str = handle_task_update(json.dumps({"task_id": task_id, "status": "in_progress"}))
        updated = json.loads(updated_str)
        self.assertEqual(updated["status"], "in_progress")

        # Record output
        output_str = handle_task_output(json.dumps({"task_id": task_id, "output": "step 1 done"}))
        with_output = json.loads(output_str)
        self.assertEqual(with_output["output"], "step 1 done")

        # Stop
        stopped_str = handle_task_stop(json.dumps({"task_id": task_id}))
        stopped = json.loads(stopped_str)
        self.assertEqual(stopped["status"], "stopped")

    def test_task_list(self) -> None:
        handle_task_create('{"name": "t1", "description": ""}')
        handle_task_create('{"name": "t2", "description": ""}')
        result = json.loads(handle_task_list(""))
        self.assertEqual(len(result), 2)

    def test_task_create_missing_name(self) -> None:
        result = handle_task_create('{"description": "no name"}')
        self.assertIn("Error", result)

    def test_task_get_not_found(self) -> None:
        result = handle_task_get('{"task_id": "does-not-exist"}')
        self.assertIn("not found", result.lower())


class TestTeamTools(unittest.TestCase):
    def setUp(self) -> None:
        _reset_stores()

    def test_team_create_delete(self) -> None:
        created_str = handle_team_create('{"name": "alpha", "members": ["agent1", "agent2"]}')
        created = json.loads(created_str)
        self.assertEqual(created["name"], "alpha")
        self.assertIn("agent1", created["member_names"])
        self.assertIn("agent2", created["member_names"])
        team_id = created["team_id"]

        deleted_result = handle_team_delete(json.dumps({"team_id": team_id}))
        self.assertIn("deleted", deleted_result.lower())

        # Confirm it's gone
        again = handle_team_delete(json.dumps({"team_id": team_id}))
        self.assertIn("not found", again.lower())

    def test_team_create_missing_name(self) -> None:
        result = handle_team_create('{"members": []}')
        self.assertIn("Error", result)


class TestAgentTools(unittest.TestCase):
    def setUp(self) -> None:
        _reset_stores()

    def test_agent_spawn_multi(self) -> None:
        payload = json.dumps({"agents": [{"prompt": "task 1"}, {"prompt": "task 2"}]})
        result_str = handle_spawn_multi_agent(payload)
        result = json.loads(result_str)
        self.assertEqual(result["spawned"], 2)
        self.assertEqual(len(result["agent_ids"]), 2)
        self.assertEqual(len(result["agents"]), 2)

    def test_agent_spawn_multi_skips_empty_prompts(self) -> None:
        payload = json.dumps({"agents": [{"prompt": "real task"}, {"prompt": ""}]})
        result = json.loads(handle_spawn_multi_agent(payload))
        self.assertEqual(result["spawned"], 1)

    def test_agent_spawn_multi_not_list(self) -> None:
        result = handle_spawn_multi_agent('{"agents": "not-a-list"}')
        self.assertIn("Error", result)


class TestWebTools(unittest.TestCase):
    def test_web_fetch_invalid_url(self) -> None:
        result = handle_web_fetch('{"url": "not-a-valid-url"}')
        self.assertIn("Error", result)

    def test_web_fetch_missing_url(self) -> None:
        result = handle_web_fetch("{}")
        self.assertIn("Error", result)


class TestTodoTool(unittest.TestCase):
    def setUp(self) -> None:
        _reset_stores()

    def test_todo_write_create_list_complete_delete(self) -> None:
        # Create a todo
        created_str = handle_todo_write('{"content": "write unit tests"}')
        created = json.loads(created_str)
        self.assertEqual(created["content"], "write unit tests")
        self.assertFalse(created["done"])
        todo_id = created["todo_id"]

        # List todos
        listed_str = handle_todo_write('{"action": "list"}')
        listed = json.loads(listed_str)
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0]["todo_id"], todo_id)

        # Complete it
        completed_str = handle_todo_write(json.dumps({"action": "complete", "todo_id": todo_id}))
        completed = json.loads(completed_str)
        self.assertTrue(completed["done"])

        # Delete it
        deleted_result = handle_todo_write(json.dumps({"action": "delete", "todo_id": todo_id}))
        self.assertIn("deleted", deleted_result.lower())

        # Confirm empty
        empty_str = handle_todo_write('{"action": "list"}')
        self.assertEqual(json.loads(empty_str), [])

    def test_todo_batch_creation(self) -> None:
        payload = json.dumps({
            "todos": [
                {"content": "item one"},
                {"content": "item two"},
            ]
        })
        result = json.loads(handle_todo_write(payload))
        self.assertEqual(len(result), 2)
        contents = [t["content"] for t in result]
        self.assertIn("item one", contents)
        self.assertIn("item two", contents)


class TestConfigTool(unittest.TestCase):
    def setUp(self) -> None:
        _reset_stores()

    def test_config_set_get(self) -> None:
        handle_config('{"action": "set", "key": "theme", "value": "dark"}')
        result = handle_config('{"action": "get", "key": "theme"}')
        self.assertEqual(result, "dark")

    def test_config_list(self) -> None:
        handle_config('{"action": "set", "key": "a", "value": "1"}')
        handle_config('{"action": "set", "key": "b", "value": "2"}')
        result = json.loads(handle_config('{"action": "list"}'))
        self.assertEqual(result["a"], "1")
        self.assertEqual(result["b"], "2")

    def test_config_get_missing_key(self) -> None:
        result = handle_config('{"action": "get"}')
        self.assertIn("Error", result)

    def test_config_set_missing_key(self) -> None:
        result = handle_config('{"action": "set", "value": "something"}')
        self.assertIn("Error", result)


class TestModeTools(unittest.TestCase):
    def setUp(self) -> None:
        _reset_stores()

    def test_mode_toggle(self) -> None:
        # Initially False
        self.assertFalse(stores.get_mode_flag("plan_mode"))

        # Enter plan mode
        result = handle_enter_plan_mode("")
        self.assertIn("activated", result.lower())
        self.assertTrue(stores.get_mode_flag("plan_mode"))

        # Exit plan mode
        result = handle_exit_plan_mode("")
        self.assertIn("deactivated", result.lower())
        self.assertFalse(stores.get_mode_flag("plan_mode"))


class TestToolSearch(unittest.TestCase):
    def test_tool_search_bash(self) -> None:
        result = handle_tool_search('{"query": "bash"}')
        self.assertIn("BashTool", result)

    def test_tool_search_no_query(self) -> None:
        result = handle_tool_search("{}")
        self.assertIn("Error", result)

    def test_tool_search_no_match(self) -> None:
        result = handle_tool_search('{"query": "zzz_totally_nonexistent_xyz"}')
        self.assertIn("No tools found", result)


if __name__ == "__main__":
    unittest.main()
