from __future__ import annotations

import unittest

from src import stores


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


class TestTaskCRUD(unittest.TestCase):
    def setUp(self) -> None:
        _reset_stores()

    def test_create_task(self) -> None:
        task = stores.create_task("my task", "a description")
        self.assertEqual(task.name, "my task")
        self.assertEqual(task.description, "a description")
        self.assertEqual(task.status, "pending")
        self.assertIsNotNone(task.task_id)

    def test_get_task(self) -> None:
        task = stores.create_task("get me", "desc")
        fetched = stores.get_task(task.task_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.task_id, task.task_id)

    def test_get_task_not_found(self) -> None:
        result = stores.get_task("nonexistent-id")
        self.assertIsNone(result)

    def test_list_tasks(self) -> None:
        self.assertEqual(len(stores.list_tasks()), 0)
        stores.create_task("t1", "")
        stores.create_task("t2", "")
        self.assertEqual(len(stores.list_tasks()), 2)

    def test_update_status(self) -> None:
        task = stores.create_task("update me", "")
        updated = stores.update_task(task.task_id, "in_progress")
        self.assertIsNotNone(updated)
        self.assertEqual(updated.status, "in_progress")

    def test_update_task_not_found(self) -> None:
        result = stores.update_task("bad-id", "in_progress")
        self.assertIsNone(result)

    def test_record_output(self) -> None:
        task = stores.create_task("output task", "")
        updated = stores.record_task_output(task.task_id, "some output text")
        self.assertIsNotNone(updated)
        self.assertEqual(updated.output, "some output text")

    def test_record_output_not_found(self) -> None:
        result = stores.record_task_output("bad-id", "output")
        self.assertIsNone(result)

    def test_stop_task(self) -> None:
        task = stores.create_task("stoppable", "")
        stopped = stores.stop_task(task.task_id)
        self.assertIsNotNone(stopped)
        self.assertEqual(stopped.status, "stopped")

    def test_stop_task_not_found(self) -> None:
        result = stores.stop_task("bad-id")
        self.assertIsNone(result)


class TestTeamCRUD(unittest.TestCase):
    def setUp(self) -> None:
        _reset_stores()

    def test_create_team(self) -> None:
        team = stores.create_team("alpha", ["alice", "bob"])
        self.assertEqual(team.name, "alpha")
        self.assertIn("alice", team.member_names)
        self.assertIn("bob", team.member_names)

    def test_get_team(self) -> None:
        team = stores.create_team("beta", [])
        fetched = stores.get_team(team.team_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.team_id, team.team_id)

    def test_get_team_not_found(self) -> None:
        result = stores.get_team("nonexistent")
        self.assertIsNone(result)

    def test_list_teams(self) -> None:
        self.assertEqual(len(stores.list_teams()), 0)
        stores.create_team("t1", [])
        stores.create_team("t2", [])
        self.assertEqual(len(stores.list_teams()), 2)

    def test_delete_team(self) -> None:
        team = stores.create_team("deletable", [])
        deleted = stores.delete_team(team.team_id)
        self.assertTrue(deleted)
        self.assertIsNone(stores.get_team(team.team_id))

    def test_delete_team_not_found(self) -> None:
        result = stores.delete_team("bad-id")
        self.assertFalse(result)


class TestAgentCRUD(unittest.TestCase):
    def setUp(self) -> None:
        _reset_stores()

    def test_create_agent(self) -> None:
        agent = stores.create_agent("do something")
        self.assertEqual(agent.prompt, "do something")
        self.assertEqual(agent.status, "running")
        self.assertIsNotNone(agent.agent_id)

    def test_create_agent_with_parent(self) -> None:
        parent = stores.create_agent("parent task")
        child = stores.create_agent("child task", parent_id=parent.agent_id)
        self.assertEqual(child.parent_id, parent.agent_id)

    def test_get_agent(self) -> None:
        agent = stores.create_agent("find me")
        fetched = stores.get_agent(agent.agent_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.agent_id, agent.agent_id)

    def test_get_agent_not_found(self) -> None:
        result = stores.get_agent("nonexistent")
        self.assertIsNone(result)

    def test_list_agents(self) -> None:
        self.assertEqual(len(stores.list_agents()), 0)
        stores.create_agent("a1")
        stores.create_agent("a2")
        self.assertEqual(len(stores.list_agents()), 2)

    def test_complete_agent(self) -> None:
        agent = stores.create_agent("completable")
        completed = stores.complete_agent(agent.agent_id, "final result")
        self.assertIsNotNone(completed)
        self.assertEqual(completed.status, "completed")
        self.assertEqual(completed.result, "final result")

    def test_complete_agent_not_found(self) -> None:
        result = stores.complete_agent("bad-id", "result")
        self.assertIsNone(result)


class TestTodoCRUD(unittest.TestCase):
    def setUp(self) -> None:
        _reset_stores()

    def test_create_todo(self) -> None:
        todo = stores.create_todo("write tests")
        self.assertEqual(todo.content, "write tests")
        self.assertFalse(todo.done)

    def test_list_todos(self) -> None:
        self.assertEqual(len(stores.list_todos()), 0)
        stores.create_todo("item 1")
        stores.create_todo("item 2")
        self.assertEqual(len(stores.list_todos()), 2)

    def test_complete_todo(self) -> None:
        todo = stores.create_todo("finish me")
        completed = stores.complete_todo(todo.todo_id)
        self.assertIsNotNone(completed)
        self.assertTrue(completed.done)

    def test_complete_todo_not_found(self) -> None:
        result = stores.complete_todo("bad-id")
        self.assertIsNone(result)

    def test_delete_todo(self) -> None:
        todo = stores.create_todo("delete me")
        deleted = stores.delete_todo(todo.todo_id)
        self.assertTrue(deleted)
        self.assertIsNone(stores.get_todo(todo.todo_id))

    def test_delete_todo_not_found(self) -> None:
        result = stores.delete_todo("bad-id")
        self.assertFalse(result)


class TestCronCRUD(unittest.TestCase):
    def setUp(self) -> None:
        _reset_stores()

    def test_create_cron(self) -> None:
        entry = stores.create_cron("0 * * * *", "echo hello")
        self.assertEqual(entry.schedule, "0 * * * *")
        self.assertEqual(entry.command, "echo hello")
        self.assertIsNotNone(entry.cron_id)

    def test_list_crons(self) -> None:
        self.assertEqual(len(stores.list_crons()), 0)
        stores.create_cron("* * * * *", "cmd1")
        stores.create_cron("0 0 * * *", "cmd2")
        self.assertEqual(len(stores.list_crons()), 2)

    def test_delete_cron(self) -> None:
        entry = stores.create_cron("* * * * *", "echo bye")
        deleted = stores.delete_cron(entry.cron_id)
        self.assertTrue(deleted)
        self.assertEqual(len(stores.list_crons()), 0)

    def test_delete_cron_not_found(self) -> None:
        result = stores.delete_cron("bad-id")
        self.assertFalse(result)


class TestConfigGetSet(unittest.TestCase):
    def setUp(self) -> None:
        _reset_stores()

    def test_set_and_get(self) -> None:
        stores.set_config("theme", "dark")
        self.assertEqual(stores.get_config("theme"), "dark")

    def test_get_default(self) -> None:
        self.assertEqual(stores.get_config("missing", "fallback"), "fallback")

    def test_get_empty_default(self) -> None:
        self.assertEqual(stores.get_config("missing"), "")

    def test_all_config(self) -> None:
        stores.set_config("a", "1")
        stores.set_config("b", "2")
        cfg = stores.all_config()
        self.assertEqual(cfg["a"], "1")
        self.assertEqual(cfg["b"], "2")

    def test_all_config_is_copy(self) -> None:
        stores.set_config("x", "original")
        cfg = stores.all_config()
        cfg["x"] = "mutated"
        self.assertEqual(stores.get_config("x"), "original")


class TestModeFlags(unittest.TestCase):
    def setUp(self) -> None:
        _reset_stores()

    def test_default_plan_mode_false(self) -> None:
        self.assertFalse(stores.get_mode_flag("plan_mode"))

    def test_default_worktree_mode_false(self) -> None:
        self.assertFalse(stores.get_mode_flag("worktree_mode"))

    def test_set_plan_mode_true(self) -> None:
        stores.set_mode_flag("plan_mode", True)
        self.assertTrue(stores.get_mode_flag("plan_mode"))

    def test_set_plan_mode_back_to_false(self) -> None:
        stores.set_mode_flag("plan_mode", True)
        stores.set_mode_flag("plan_mode", False)
        self.assertFalse(stores.get_mode_flag("plan_mode"))

    def test_set_worktree_mode(self) -> None:
        stores.set_mode_flag("worktree_mode", True)
        self.assertTrue(stores.get_mode_flag("worktree_mode"))

    def test_get_unknown_flag_returns_false(self) -> None:
        self.assertFalse(stores.get_mode_flag("nonexistent_flag"))


if __name__ == "__main__":
    unittest.main()
