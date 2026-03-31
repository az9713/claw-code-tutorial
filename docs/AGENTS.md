# Agent Architecture: A Complete Technical Reference

This document is a full extraction of everything the codebase reveals about agents, the agent harness, and agentic workflows. It covers both the active Python implementation and the architectural picture surfaced by the TypeScript snapshot metadata.

---

## Table of Contents

1. [Overview: What the Harness Is](#1-overview-what-the-harness-is)
2. [The AgentTool Subsystem](#2-the-agenttool-subsystem)
3. [Built-in Specialized Agents](#3-built-in-specialized-agents)
4. [Multi-Agent Infrastructure](#4-multi-agent-infrastructure)
5. [Task Management Tools](#5-task-management-tools)
6. [Team and Inter-Agent Communication](#6-team-and-inter-agent-communication)
7. [The Coordinator Mode](#7-the-coordinator-mode)
8. [The Bootstrap Lifecycle](#8-the-bootstrap-lifecycle)
9. [The Runtime: PortRuntime](#9-the-runtime-portruntime)
10. [The Query Engine: Turn-Based Agentic Loop](#10-the-query-engine-turn-based-agentic-loop)
11. [Streaming Event Protocol](#11-streaming-event-protocol)
12. [Token Budget and Compaction](#12-token-budget-and-compaction)
13. [The Tool Pool: What Agents Can Use](#13-the-tool-pool-what-agents-can-use)
14. [The Command System](#14-the-command-system)
15. [Permission and Trust Architecture](#15-permission-and-trust-architecture)
16. [Deferred Initialisation and Trust Gating](#16-deferred-initialisation-and-trust-gating)
17. [Session Lifecycle and Persistence](#17-session-lifecycle-and-persistence)
18. [History and Audit Trail](#18-history-and-audit-trail)
19. [Cost Tracking](#19-cost-tracking)
20. [Prefetch and Workspace Initialisation](#20-prefetch-and-workspace-initialisation)
21. [Remote Runtime Modes](#21-remote-runtime-modes)
22. [The Bridge Layer](#22-the-bridge-layer)
23. [The Services Layer](#23-the-services-layer)
24. [Skills as Agent Extensions](#24-skills-as-agent-extensions)
25. [Hooks System](#25-hooks-system)
26. [Application State for Multi-Agent Views](#26-application-state-for-multi-agent-views)
27. [Complete Tool Inventory: Agent-Related Tools](#27-complete-tool-inventory-agent-related-tools)
28. [Complete Command Inventory: Agent-Related Commands](#28-complete-command-inventory-agent-related-commands)
29. [Current Agent Implementation State](#29-current-agent-implementation-state)
30. [Architectural Summary](#30-architectural-summary)

---

## 1. Overview: What the Harness Is

The Claude Code agent harness is a **turn-based orchestration system** that:

- Loads a registry of commands (207 entries) and tools (184 entries) at startup
- Routes free-text prompts to matching commands and tools using token scoring
- Executes a multi-turn conversation loop with token budget enforcement
- Spawns and manages subagents that can each run their own conversation loops
- Manages sessions (persistence, resumption, transcript compaction)
- Enforces tool permissions via deny-list contexts
- Supports distributed execution via remote, SSH, and Teleport modes

The Python codebase (`src/`) is a clean-room port of the original TypeScript system. The TypeScript architecture is fully described in `src/reference_data/` — 30 subsystem JSON files, plus complete command and tool snapshot manifests. The Python code implements the runtime skeleton; the reference data reveals the full scope of what the original harness did.

---

## 2. The AgentTool Subsystem

The most important agentic component in the tool inventory is `AgentTool` — a dedicated subsystem with **18 TypeScript modules** under `tools/AgentTool/`. Each module is tracked in `src/reference_data/tools_snapshot.json`.

### Core modules

| Module | Source path | Purpose |
|--------|-------------|---------|
| `AgentTool` | `tools/AgentTool/AgentTool.tsx` | Main agent tool React component; the top-level entry point for invoking agents |
| `UI` | `tools/AgentTool/UI.tsx` | Agent UI renderer component |
| `prompt` | `tools/AgentTool/prompt.ts` | Prompt templates for agent invocations |
| `constants` | `tools/AgentTool/constants.ts` | Shared constants (timeouts, limits, identifiers) |
| `agentToolUtils` | `tools/AgentTool/agentToolUtils.ts` | Utility functions for agent tool operations |
| `builtInAgents` | `tools/AgentTool/builtInAgents.ts` | Registry of all built-in agent definitions |

### Agent lifecycle modules

| Module | Source path | Purpose |
|--------|-------------|---------|
| `runAgent` | `tools/AgentTool/runAgent.ts` | Core agent execution function — starts a new agent run |
| `forkSubagent` | `tools/AgentTool/forkSubagent.ts` | Forks the current context into a child subagent |
| `resumeAgent` | `tools/AgentTool/resumeAgent.ts` | Resumes a previously suspended or interrupted agent |
| `loadAgentsDir` | `tools/AgentTool/loadAgentsDir.ts` | Loads custom agent definitions from a project's agents directory |

### Agent memory modules

| Module | Source path | Purpose |
|--------|-------------|---------|
| `agentMemory` | `tools/AgentTool/agentMemory.ts` | In-session memory state for a running agent |
| `agentMemorySnapshot` | `tools/AgentTool/agentMemorySnapshot.ts` | Point-in-time snapshot of agent memory (for resumption or branching) |

### Agent display modules

| Module | Source path | Purpose |
|--------|-------------|---------|
| `agentDisplay` | `tools/AgentTool/agentDisplay.ts` | Rendering/formatting of agent output in the terminal UI |
| `agentColorManager` | `tools/AgentTool/agentColorManager.ts` | Colour assignment for distinguishing multiple concurrent agents in the display |

The colour management and display modules suggest that the original system can run **multiple concurrent agents visually distinguished by colour** in the terminal.

---

## 3. Built-in Specialized Agents

Five purpose-built agents are registered under `tools/AgentTool/built-in/`. They are managed by `builtInAgents.ts` and loaded as part of the tool snapshot.

### `exploreAgent`
**Source:** `tools/AgentTool/built-in/exploreAgent.ts`

A fast codebase exploration agent. Specialised for searching files by pattern, grepping for keywords, and answering structural questions about a repository. Optimised for high-throughput read operations — not for writing or editing code.

### `planAgent`
**Source:** `tools/AgentTool/built-in/planAgent.ts`

A software architect agent. Analyses requirements, identifies critical files, considers trade-offs, and produces step-by-step implementation plans. Takes a design or requirement as input and returns a structured plan that can guide subsequent implementation agents.

### `generalPurposeAgent`
**Source:** `tools/AgentTool/built-in/generalPurposeAgent.ts`

A broad-scope agent for multi-step tasks: researching complex questions, searching code, executing sequences of file reads and modifications. Used when a task requires reasoning across multiple steps but does not map cleanly to a specialised agent type.

### `claudeCodeGuideAgent`
**Source:** `tools/AgentTool/built-in/claudeCodeGuideAgent.ts`

An agent specialised in answering questions about Claude Code itself — its CLI features, slash commands, MCP server integration, settings, IDE extensions, keyboard shortcuts, and the Claude API/Anthropic SDK. Acts as an in-process documentation assistant.

### `verificationAgent`
**Source:** `tools/AgentTool/built-in/verificationAgent.ts`

A quality-assurance agent. Reviews completed work against a plan or set of requirements, identifies issues, and provides actionable feedback with severity ratings. Invoked after implementation steps complete to validate correctness before marking work done.

### `statuslineSetup`
**Source:** `tools/AgentTool/built-in/statuslineSetup.ts`

A configuration agent specialised for setting up the Claude Code status line. Uses only `Read` and `Edit` tools.

---

## 4. Multi-Agent Infrastructure

### `spawnMultiAgent`
**Source:** `tools/shared/spawnMultiAgent.ts`

The primary mechanism for launching multiple agents in parallel. Lives in `tools/shared/` rather than `tools/AgentTool/`, indicating it is a cross-cutting utility rather than part of the agent tool specifically.

The existence of this module — alongside `agentColorManager` — confirms that the harness is designed for **true parallel multi-agent execution**: multiple agents running concurrently, each with their own context, distinguished by colour in the shared terminal display.

### `forkSubagent`
**Source:** `tools/AgentTool/forkSubagent.ts`

Forks the current agent's execution context into a child subagent. The parent agent can then wait for, monitor, or receive results from the child. This is the mechanism for **hierarchical agent delegation** — a parent agent delegates a subtask to a forked child that runs its own loop.

### `loadAgentsDir`
**Source:** `tools/AgentTool/loadAgentsDir.ts`

Scans the project for a user-defined agents directory and loads custom agent definitions from it. This makes the agent registry **extensible** — project teams can define their own agents alongside the built-in ones.

---

## 5. Task Management Tools

The harness includes a dedicated **task management tool suite** with six tools. These enable agents to create, track, and coordinate units of work — the foundation of multi-step agentic workflows.

Each tool lives in its own directory with a main implementation file, a `constants.ts`, a `prompt.ts` (prompt template), and sometimes a `UI.tsx` component.

| Tool | Source | Purpose |
|------|--------|---------|
| `TaskCreateTool` | `tools/TaskCreateTool/TaskCreateTool.ts` | Creates a new task with a title, description, and status |
| `TaskGetTool` | `tools/TaskGetTool/TaskGetTool.ts` | Retrieves the details of a specific task by ID |
| `TaskListTool` | `tools/TaskListTool/TaskListTool.ts` | Lists all tasks, with filtering and pagination |
| `TaskUpdateTool` | `tools/TaskUpdateTool/TaskUpdateTool.ts` | Updates a task's status or properties (e.g., mark `in_progress`, `completed`) |
| `TaskOutputTool` | `tools/TaskOutputTool/TaskOutputTool.tsx` | Reads the output/result associated with a task; has a React UI component |
| `TaskStopTool` | `tools/TaskStopTool/TaskStopTool.ts` | Stops (cancels) a running task; has both `UI.tsx` and `prompt.ts` sub-modules |

The task tools correspond directly to the `TaskCreate`, `TaskGet`, `TaskList`, `TaskUpdate`, `TaskOutput`, `TaskStop` tools visible in the current Claude Code skill system.

**There is also a commands-level interface to tasks:**
- `tasks` command (`commands/tasks/index.ts`) — CLI entry point
- `tasks` component (`commands/tasks/tasks.tsx`) — React UI for the tasks view

### `PortingTask` (`src/task.py`)

The Python port introduces a lightweight `PortingTask` dataclass:

```python
@dataclass(frozen=True)
class PortingTask:
    name: str
    description: str
```

`src/tasks.py` defines three default porting tasks:

```python
def default_tasks() -> list[PortingTask]:
    return [
        PortingTask('root-module-parity', 'Mirror the root module surface of the archived snapshot'),
        PortingTask('directory-parity', 'Mirror top-level subsystem names as Python packages'),
        PortingTask('parity-audit', 'Continuously measure parity against the local archive'),
    ]
```

These are porting-domain tasks, not the general-purpose runtime task system. The full task system lives in the TypeScript tool suite.

---

## 6. Team and Inter-Agent Communication

Three tools implement multi-agent team collaboration:

### `SendMessageTool`
**Source:** `tools/SendMessageTool/SendMessageTool.ts` + `UI.tsx` + `constants.ts` + `prompt.ts`

Sends a message from one agent to another (or to the user). Enables agents running in parallel to communicate — passing results, requesting information, or signalling completion. The presence of a UI component (`UI.tsx`) indicates that sent messages are rendered in the terminal display.

### `TeamCreateTool`
**Source:** `tools/TeamCreateTool/TeamCreateTool.ts` + `UI.tsx` + `constants.ts` + `prompt.ts`

Creates a named team of agents. A team is an organisational grouping that allows an orchestrating agent to spawn, address, and coordinate a set of worker agents collectively.

### `TeamDeleteTool`
**Source:** `tools/TeamDeleteTool/TeamDeleteTool.ts` + `UI.tsx` + `constants.ts` + `prompt.ts`

Dissolves a team. Cleans up the team grouping and presumably handles teardown of any member agents or shared resources.

The team model — CreateTeam → SendMessage → DeleteTeam — describes a **named, managed group of collaborating agents** with a clear lifecycle.

There is also an **agents command** at the UI level:
- `agents` (`commands/agents/agents.tsx`) — React component listing/managing active agents
- `agents` (`commands/agents/index.ts`) — CLI index/router for the agents command

---

## 7. The Coordinator Mode

### `coordinatorMode`
**Source:** `coordinator/coordinatorMode.ts` (1-module subsystem)

The `coordinator` subsystem has a single file: `coordinatorMode.ts`. This is the coordinator mode of the harness.

In the hooks system (`hooks.json`), there is a `toolPermission/coordinator` handler — a hook that fires on tool permission checks specifically when operating in coordinator mode. This indicates that coordinator mode has **different permission semantics** from interactive mode.

The hooks system also references a `toolPermission/swarmWorker` handler, which together with `coordinator` suggests a **two-role multi-agent model**:

- **Coordinator**: orchestrates work, issues tasks to workers, has broader permissions
- **Swarm Worker**: executes delegated tasks under tighter permission constraints set by the coordinator

This pattern — coordinator dispatching to swarm workers — is a classic hierarchical multi-agent architecture where a single top-level agent manages a fleet of specialised sub-workers.

---

## 8. The Bootstrap Lifecycle

When the harness starts, it executes a **7-stage bootstrap sequence** defined in `src/bootstrap_graph.py`:

```python
stages = (
    'top-level prefetch side effects',
    'warning handler and environment guards',
    'CLI parser and pre-action trust gate',
    'setup() + commands/agents parallel load',
    'deferred init after trust',
    'mode routing: local / remote / ssh / teleport / direct-connect / deep-link',
    'query engine submit loop',
)
```

### Stage-by-stage breakdown

**Stage 1 — Top-level prefetch side effects**

Three prefetch operations run before anything else (`src/prefetch.py`):
- `start_mdm_raw_read()` — reads MDM (Mobile Device Management) policy. This indicates the harness runs in managed enterprise environments and must respect device policies before startup.
- `start_keychain_prefetch()` — warms the keychain (API credentials, tokens). Running this early avoids latency on the first API call.
- `start_project_scan(root)` — scans the project root directory to count files and detect archive availability.

These three run in parallel in the original TypeScript system (the stage description says "parallel load" explicitly in Stage 4; Stage 1 starts async side effects that resolve later).

**Stage 2 — Warning handler and environment guards**

Environment validation runs before user-facing interaction: checking Python/Node version compatibility, platform guards, and attaching a warning handler that captures runtime warnings and surfaces them to the user.

**Stage 3 — CLI parser and pre-action trust gate**

The CLI parser runs, identifying the subcommand and flags. Crucially, a **trust gate** fires here. The `trusted` boolean (from `run_setup(trusted=True/False)`) controls whether the session is allowed to initialise plugins, skills, MCP connections, and session hooks. This happens before any agent execution, so untrusted contexts never reach the live tool-loading stage.

**Stage 4 — setup() + commands/agents parallel load**

`run_setup()` runs (capturing Python version, platform, prefetch results, deferred init state). Simultaneously, the command snapshot and tool snapshot are loaded from JSON (`load_command_snapshot()` / `load_tool_snapshot()`, both cached with `lru_cache`). The stage description explicitly names this as `commands/agents parallel load`, indicating the original TypeScript loaded the agent registry concurrently with the command registry.

The startup steps (`WorkspaceSetup.startup_steps()`) enumerate the six internal steps:
1. Start top-level prefetch side effects
2. Build workspace context
3. Load mirrored command snapshot
4. Load mirrored tool snapshot
5. Prepare parity audit hooks
6. Apply trust-gated deferred init

**Stage 5 — Deferred init after trust**

After the trust gate passes, `run_deferred_init(trusted=True)` enables four subsystems:
- `plugin_init` — loads plugin definitions
- `skill_init` — loads skills (the bundled skill library)
- `mcp_prefetch` — initiates MCP server connections
- `session_hooks` — registers lifecycle hooks (startup, shutdown, tool-permission handlers)

**Stage 6 — Mode routing**

The runtime branches based on how the harness was invoked:
- **local** — standard interactive or scripted mode
- **remote** — remote control via the bridge layer
- **ssh** — SSH proxy mode
- **teleport** — Teleport-based cluster access
- **direct-connect** — direct session connection
- **deep-link** — launched via a deep link URL

Each mode is handled by a dedicated handler (see §21).

**Stage 7 — Query engine submit loop**

The `QueryEnginePort` submit loop begins. This is the **agentic heart of the system**: the turn-by-turn conversation loop that receives prompts, matches commands and tools, enforces budgets, compacts history, and persists sessions.

---

## 9. The Runtime: PortRuntime

`PortRuntime` (`src/runtime.py`) is the orchestration layer that sits between the CLI and the query engine. It is **stateless** — each method call creates all necessary state from scratch.

### `route_prompt(prompt, limit=5) → list[RoutedMatch]`

Token-scores a free-text prompt against every registered command and tool.

```python
def route_prompt(self, prompt: str, limit: int = 5) -> list[RoutedMatch]:
    tokens = {token.lower() for token in prompt.replace('/', ' ').replace('-', ' ').split() if token}
    by_kind = {
        'command': self._collect_matches(tokens, PORTED_COMMANDS, 'command'),
        'tool': self._collect_matches(tokens, PORTED_TOOLS, 'tool'),
    }
    selected: list[RoutedMatch] = []
    for kind in ('command', 'tool'):
        if by_kind[kind]:
            selected.append(by_kind[kind].pop(0))
    leftovers = sorted(
        [match for matches in by_kind.values() for match in matches],
        key=lambda item: (-item.score, item.kind, item.name),
    )
    selected.extend(leftovers[: max(0, limit - len(selected))])
    return selected[:limit]
```

**Scoring algorithm** (`_score`): For each token in the prompt, checks whether it appears as a substring in the module's `name`, `source_hint`, or `responsibility`. The score is the count of matching tokens.

**Selection logic**: Guarantees diversity — at least one command match and one tool match appear in the results if available, before filling remaining slots by raw score.

Each match is a `RoutedMatch(kind, name, source_hint, score)`.

### `bootstrap_session(prompt, limit=5) → RuntimeSession`

Runs the full harness lifecycle for a single prompt:

1. Builds `PortContext` (file counts, archive availability)
2. Runs `run_setup(trusted=True)` — all prefetches and deferred inits
3. Creates a `HistoryLog` to track the session audit trail
4. Constructs a `QueryEnginePort` from the workspace manifest
5. Routes the prompt → `list[RoutedMatch]`
6. Executes all matching command shims via `ExecutionRegistry`
7. Executes all matching tool shims via `ExecutionRegistry`
8. Infers permission denials (bash tools automatically gated)
9. Streams events via `stream_submit_message()`
10. Submits the message via `submit_message()` → `TurnResult`
11. Persists the session to `.port_sessions/`
12. Logs all steps to `HistoryLog`

Returns `RuntimeSession` — a complete, immutable record of the session.

### `run_turn_loop(prompt, limit=5, max_turns=3, structured_output=False) → list[TurnResult]`

Drives a stateful multi-turn loop:

```python
def run_turn_loop(self, prompt, limit=5, max_turns=3, structured_output=False):
    engine = QueryEnginePort.from_workspace()
    engine.config = QueryEngineConfig(max_turns=max_turns, structured_output=structured_output)
    matches = self.route_prompt(prompt, limit=limit)
    command_names = tuple(match.name for match in matches if match.kind == 'command')
    tool_names = tuple(match.name for match in matches if match.kind == 'tool')
    results = []
    for turn in range(max_turns):
        turn_prompt = prompt if turn == 0 else f'{prompt} [turn {turn + 1}]'
        result = engine.submit_message(turn_prompt, command_names, tool_names, ())
        results.append(result)
        if result.stop_reason != 'completed':
            break
    return results
```

Key observations:
- Routing happens **once** at the start; subsequent turns reuse the same command/tool set
- The loop stops on any `stop_reason` other than `'completed'`
- Turn prompts after the first are annotated with `[turn N]` — a simple continuation signal
- The `QueryEnginePort` is shared across all turns, so `mutable_messages`, `total_usage`, and `transcript_store` accumulate across the loop

### `_infer_permission_denials`

```python
def _infer_permission_denials(self, matches: list[RoutedMatch]) -> list[PermissionDenial]:
    denials = []
    for match in matches:
        if match.kind == 'tool' and 'bash' in match.name.lower():
            denials.append(PermissionDenial(
                tool_name=match.name,
                reason='destructive shell execution remains gated in the Python port'
            ))
    return denials
```

Any matched tool whose name contains `"bash"` is automatically denied. This is an unconditional safety gate that mirrors the original harness's approach to destructive shell operations — they require explicit permission grant, not just being in the tool pool.

---

## 10. The Query Engine: Turn-Based Agentic Loop

`QueryEnginePort` (`src/query_engine.py`) is the agentic conversation engine. It manages mutable state across turns.

### Configuration

```python
@dataclass(frozen=True)
class QueryEngineConfig:
    max_turns: int = 8
    max_budget_tokens: int = 2000
    compact_after_turns: int = 12
    structured_output: bool = False
    structured_retry_limit: int = 2
```

### `submit_message` — core turn execution

```python
def submit_message(self, prompt, matched_commands=(), matched_tools=(), denied_tools=()):
    # 1. Hard stop if max turns reached
    if len(self.mutable_messages) >= self.config.max_turns:
        return TurnResult(..., stop_reason='max_turns_reached')

    # 2. Build the output summary for this turn
    summary_lines = [
        f'Prompt: {prompt}',
        f'Matched commands: {", ".join(matched_commands) or "none"}',
        f'Matched tools: {", ".join(matched_tools) or "none"}',
        f'Permission denials: {len(denied_tools)}',
    ]
    output = self._format_output(summary_lines)  # plain text or JSON

    # 3. Project token usage
    projected_usage = self.total_usage.add_turn(prompt, output)
    stop_reason = 'completed'
    if projected_usage.input_tokens + projected_usage.output_tokens > self.config.max_budget_tokens:
        stop_reason = 'max_budget_reached'

    # 4. Commit state
    self.mutable_messages.append(prompt)
    self.transcript_store.append(prompt)
    self.permission_denials.extend(denied_tools)
    self.total_usage = projected_usage

    # 5. Compact if needed
    self.compact_messages_if_needed()

    return TurnResult(prompt, output, matched_commands, matched_tools, denied_tools,
                      projected_usage, stop_reason)
```

The `TurnResult` produced at each step contains:
- Which commands and tools were matched
- Which tools were denied (and why)
- Cumulative token usage
- Why the loop stopped (`completed`, `max_turns_reached`, `max_budget_reached`)

### Structured output mode

When `structured_output=True`, each turn's output is a JSON document:

```json
{
  "summary": ["Prompt: ...", "Matched commands: ...", "..."],
  "session_id": "<hex uuid>"
}
```

JSON serialisation is retried up to `structured_retry_limit` times (default 2), then raises `RuntimeError`.

---

## 11. Streaming Event Protocol

`stream_submit_message()` is the event-streaming variant of `submit_message`. It is a generator that yields typed event dictionaries before, during, and after turn execution.

### Event sequence

```python
def stream_submit_message(self, prompt, matched_commands=(), matched_tools=(), denied_tools=()):
    yield {'type': 'message_start', 'session_id': self.session_id, 'prompt': prompt}

    if matched_commands:
        yield {'type': 'command_match', 'commands': matched_commands}

    if matched_tools:
        yield {'type': 'tool_match', 'tools': matched_tools}

    if denied_tools:
        yield {'type': 'permission_denial', 'denials': [d.tool_name for d in denied_tools]}

    result = self.submit_message(prompt, matched_commands, matched_tools, denied_tools)

    yield {'type': 'message_delta', 'text': result.output}

    yield {
        'type': 'message_stop',
        'usage': {'input_tokens': result.usage.input_tokens, 'output_tokens': result.usage.output_tokens},
        'stop_reason': result.stop_reason,
        'transcript_size': len(self.transcript_store.entries),
    }
```

### Event types

| Type | Fields | When emitted |
|------|--------|--------------|
| `message_start` | `session_id`, `prompt` | Always, first |
| `command_match` | `commands: tuple[str]` | Only when ≥1 command matched |
| `tool_match` | `tools: tuple[str]` | Only when ≥1 tool matched |
| `permission_denial` | `denials: list[str]` | Only when ≥1 tool denied |
| `message_delta` | `text: str` | Always, after state committed |
| `message_stop` | `usage`, `stop_reason`, `transcript_size` | Always, last |

This event protocol mirrors the Anthropic streaming API's own event taxonomy (`message_start`, `content_block_delta`, `message_stop`) — suggesting the harness was designed to sit between the CLI and the API in a streaming pipeline.

---

## 12. Token Budget and Compaction

### Budget enforcement

Token counting uses a **word-count approximation** (`len(text.split())`), not BPE tokenisation. This is a fast, dependency-free heuristic sufficient for the porting workspace's purposes; the original TypeScript system would use exact token counts from the API.

```python
def add_turn(self, prompt: str, output: str) -> 'UsageSummary':
    return UsageSummary(
        input_tokens=self.input_tokens + len(prompt.split()),
        output_tokens=self.output_tokens + len(output.split()),
    )
```

When `projected_usage.input_tokens + projected_usage.output_tokens > max_budget_tokens`, the turn still executes and its result is recorded, but `stop_reason` is set to `'max_budget_reached'`. The calling loop in `run_turn_loop` then stops (since `stop_reason != 'completed'`).

### Message compaction

```python
def compact_messages_if_needed(self) -> None:
    if len(self.mutable_messages) > self.config.compact_after_turns:
        self.mutable_messages[:] = self.mutable_messages[-self.config.compact_after_turns:]
    self.transcript_store.compact(self.config.compact_after_turns)
```

When the turn count exceeds `compact_after_turns` (default 12), both `mutable_messages` and `transcript_store` are truncated to the most recent `compact_after_turns` entries. This is a sliding-window compaction strategy — older context is discarded to prevent unbounded memory growth across long sessions.

The `TranscriptStore` compaction (`src/transcript.py`):

```python
def compact(self, keep_last: int = 10) -> None:
    if len(self.entries) > keep_last:
        self.entries[:] = self.entries[-keep_last:]
```

---

## 13. The Tool Pool: What Agents Can Use

`ToolPool` (`src/tool_pool.py`) is the assembled set of tools available to an agent at runtime.

```python
@dataclass(frozen=True)
class ToolPool:
    tools: tuple[PortingModule, ...]
    simple_mode: bool
    include_mcp: bool
```

### `simple_mode`

When `simple_mode=True`, the tool pool is restricted to exactly three tools:
- `BashTool` — shell execution
- `FileReadTool` — file reading
- `FileEditTool` — file editing

This is the **minimal agent configuration** — just enough to read and write files and run commands. It corresponds to lightweight task execution where full tool access is not needed (and would add unnecessary overhead or risk).

### MCP tool inclusion

When `include_mcp=False`, all tools whose name or source path contains `"mcp"` are excluded. This allows running agents in environments without an active MCP server.

### Permission-based filtering

`ToolPermissionContext` (`src/permissions.py`) provides a deny-list filter on top of the base tool set:

```python
@dataclass(frozen=True)
class ToolPermissionContext:
    deny_names: frozenset[str]        # exact name matches (case-insensitive)
    deny_prefixes: tuple[str, ...]    # prefix matches (case-insensitive)

    def blocks(self, tool_name: str) -> bool:
        lowered = tool_name.lower()
        return lowered in self.deny_names or any(lowered.startswith(p) for p in self.deny_prefixes)
```

The filtering pipeline for tool pool assembly:

```
PORTED_TOOLS (184 entries)
    │
    ▼ simple_mode filter (optional: keep only BashTool, FileReadTool, FileEditTool)
    │
    ▼ MCP filter (optional: drop tools with "mcp" in name/source_hint)
    │
    ▼ PermissionContext filter (drop deny_names + deny_prefix matches)
    │
    ▼
ToolPool.tools (final set available to the agent)
```

---

## 14. The Command System

Commands are distinct from tools. They represent **user-facing operations** (slash commands, UI actions) rather than programmatic capabilities. 207 commands are tracked in `src/reference_data/commands_snapshot.json`.

The `CommandGraph` (`src/command_graph.py`) classifies all commands into three categories:

```python
@dataclass(frozen=True)
class CommandGraph:
    builtins: tuple[PortingModule, ...]    # core harness commands
    plugin_like: tuple[PortingModule, ...]  # commands from plugin source paths
    skill_like: tuple[PortingModule, ...]   # commands from skills source paths
```

Classification is based on `source_hint`:
- Contains `"plugin"` → `plugin_like`
- Contains `"skills"` → `skill_like`
- Neither → `builtins`

This three-way split reflects the extensibility model: core commands ship with the harness; additional commands are contributed by plugins or skills.

---

## 15. Permission and Trust Architecture

The permission model has three layers:

### Layer 1: ToolPermissionContext (deny-list)

Applied at tool pool assembly time. Blocks specific tools or tool prefixes from being included in the pool available to an agent. Set via CLI flags (`--deny-tool`, `--deny-prefix`) or programmatically.

### Layer 2: Automatic bash gating (PortRuntime)

Applied at routing time. Any tool whose name contains `"bash"` is automatically denied in `_infer_permission_denials()`, regardless of the `ToolPermissionContext`. This mirrors the original harness's treatment of shell execution as a specially-guarded capability.

### Layer 3: Mode-specific permission hooks (Hooks system)

The `hooks.json` subsystem reveals three `toolPermission` hooks:
- `toolPermission/coordinator` — handles permission checks in coordinator mode
- `toolPermission/interactive` — handles permission checks in interactive (human-in-the-loop) mode
- `toolPermission/swarmWorker` — handles permission checks in swarm worker mode

These suggest the permission model is **role-aware**: the same tool may be allowed for a coordinator but denied for a swarm worker, or it may be allowed in interactive mode (where a human can approve) but denied in autonomous mode.

The `deferred_init`'s `session_hooks=True` flag is what enables these permission hooks at runtime.

---

## 16. Deferred Initialisation and Trust Gating

`run_deferred_init(trusted: bool)` (`src/deferred_init.py`) controls four subsystems gated by the trust level of the session:

```python
@dataclass(frozen=True)
class DeferredInitResult:
    trusted: bool
    plugin_init: bool
    skill_init: bool
    mcp_prefetch: bool
    session_hooks: bool
```

When `trusted=False`, all four are `False`. When `trusted=True`, all four are `True`.

The trust decision is made at Stage 3 of the bootstrap (the pre-action trust gate) — before any tool loading or agent execution. An untrusted session receives:
- No plugins loaded
- No skills loaded
- No MCP server connections
- No lifecycle hooks registered

This is a strict defence-in-depth approach: an agent session initiated by an unverified source cannot load extension code, cannot connect to external MCP tools, and cannot register hooks that observe or intercept the session lifecycle.

---

## 17. Session Lifecycle and Persistence

An agent session has a well-defined lifecycle:

```
                  ┌──────────────────────────────┐
                  │   QueryEnginePort.from_       │
                  │   workspace()                │
                  │   → fresh UUID               │
                  └──────────────┬───────────────┘
                                 │
                                 ▼ turns 1..N
                  ┌──────────────────────────────┐
                  │   submit_message()           │
                  │   → mutable_messages grows   │
                  │   → total_usage accumulates  │
                  │   → transcript_store grows   │
                  └──────────────┬───────────────┘
                                 │
                         compact if needed
                                 │
                                 ▼
                  ┌──────────────────────────────┐
                  │   persist_session()          │
                  │   → flush_transcript()       │
                  │   → save_session()           │
                  │   → .port_sessions/uuid.json │
                  └──────────────┬───────────────┘
                                 │
                                 ▼  (later)
                  ┌──────────────────────────────┐
                  │   from_saved_session(uuid)   │
                  │   → load_session()           │
                  │   → restore messages +       │
                  │     usage + transcript       │
                  └──────────────────────────────┘
```

### Stored session format

```json
{
  "session_id": "<32-char hex uuid>",
  "messages": ["prompt 1", "prompt 2", "..."],
  "input_tokens": 42,
  "output_tokens": 17
}
```

Sessions are stored in `.port_sessions/` (in the current working directory). Resumption via `QueryEnginePort.from_saved_session()` rehydrates the engine with the prior message history, usage totals, and a pre-flushed transcript (restoring turn state fully).

---

## 18. History and Audit Trail

`HistoryLog` (`src/history.py`) is a session-scoped ordered event log. Unlike the transcript (which stores only prompts), the history log stores named events with structured detail strings.

```python
@dataclass(frozen=True)
class HistoryEvent:
    title: str
    detail: str

@dataclass
class HistoryLog:
    events: list[HistoryEvent]

    def add(self, title: str, detail: str) -> None: ...
    def as_markdown(self) -> str: ...
```

During `bootstrap_session()`, six named events are recorded:

| Event title | Detail content |
|-------------|----------------|
| `context` | `python_files=N, archive_available=True/False` |
| `registry` | `commands=207, tools=184` |
| `routing` | `matches=N for prompt=<prompt>` |
| `execution` | `command_execs=N tool_execs=N` |
| `turn` | `commands=N tools=N denials=N stop=<reason>` |
| `session_store` | `<path to .json file>` |

This log is the **audit trail** of what the agent did during a session: what it found, what it ran, what was denied, and where the session was saved.

---

## 19. Cost Tracking

`CostTracker` (`src/cost_tracker.py`) is a lightweight event-based cost accounting mechanism:

```python
@dataclass
class CostTracker:
    total_units: int = 0
    events: list[str] = field(default_factory=list)

    def record(self, label: str, units: int) -> None:
        self.total_units += units
        self.events.append(f'{label}:{units}')
```

Each recorded event is `"label:N"` where `N` is a unit count. `total_units` is the running sum.

`UsageSummary` (in `src/models.py`) provides complementary token-level accounting:

```python
@dataclass(frozen=True)
class UsageSummary:
    input_tokens: int = 0
    output_tokens: int = 0

    def add_turn(self, prompt: str, output: str) -> 'UsageSummary':
        return UsageSummary(
            input_tokens=self.input_tokens + len(prompt.split()),
            output_tokens=self.output_tokens + len(output.split()),
        )
```

`UsageSummary` is immutable and produces a new instance on each turn — the accumulation is tracked in `QueryEnginePort.total_usage`.

The `costHook.py` module (`apply_cost_hook()`) is a hook that applies cost tracking to a tracker instance — the integration point between the session lifecycle and cost accounting.

---

## 20. Prefetch and Workspace Initialisation

Three prefetch operations run at Stage 1 of bootstrap (`src/prefetch.py`):

| Prefetch | Simulated behaviour | Original purpose |
|----------|---------------------|-----------------|
| `start_mdm_raw_read()` | Returns placeholder result | Reads MDM (Mobile Device Management) policy before startup — relevant in enterprise deployments |
| `start_keychain_prefetch()` | Returns placeholder result | Warms keychain/credential store so API tokens are available without latency on first use |
| `start_project_scan(root)` | Scans actual filesystem | Counts source/test/asset files, detects archive presence, builds `PortContext` |

The project scan produces a `PortContext`:

```python
@dataclass(frozen=True)
class PortContext:
    source_root: Path
    tests_root: Path
    assets_root: Path
    archive_root: Path          # archive/claude_code_ts_snapshot/src
    python_file_count: int
    test_file_count: int
    asset_file_count: int
    archive_available: bool     # True if archive_root exists on disk
```

The `archive_root` path — `archive/claude_code_ts_snapshot/src` — is hardcoded, indicating the harness knows exactly where the original TypeScript source would reside if present.

---

## 21. Remote Runtime Modes

Stage 6 of the bootstrap routes the session into one of six modes. Five are non-local (`src/remote_runtime.py`, `src/direct_modes.py`):

```python
@dataclass(frozen=True)
class RuntimeModeReport:
    mode: str
    connected: bool
    detail: str
```

| Mode | Function | Detail |
|------|----------|--------|
| `remote` | `run_remote_mode(target)` | Remote control — agent runs on a remote host, controlled via the bridge |
| `ssh` | `run_ssh_mode(target)` | SSH proxy — agent communication tunnelled over SSH |
| `teleport` | `run_teleport_mode(target)` | Teleport — uses HashiCorp Teleport for zero-trust cluster access; supports resume/create |
| `direct-connect` | `run_direct_connect(target)` | Direct session connection to a named workspace |
| `deep-link` | `run_deep_link(target)` | Launched via a URL deep link — enables third-party integrations to open agent sessions |

The presence of **Teleport** (an enterprise-grade zero-trust access platform) indicates the harness is designed for production enterprise deployments where engineers access remote development environments via managed identity and policy.

---

## 22. The Bridge Layer

The `bridge` subsystem has **31 modules** — the second-largest subsystem after `utils`. Key modules from `src/reference_data/subsystems/bridge.json`:

| Module | Purpose |
|--------|---------|
| `bridgeMain.ts` | Entry point for the bridge process |
| `bridgeApi.ts` | API surface exposed by the bridge |
| `bridgeConfig.ts` | Bridge configuration |
| `bridgeDebug.ts` | Debug utilities |
| `remoteBridgeCore.ts` | Core remote bridge logic — the main bidirectional channel |
| `createSession.ts` | Creates a new bridge session |
| `codeSessionApi.ts` | Code session API |

The bridge layer is the **inter-process communication backbone** that connects:
- Local CLI ↔ remote agent instances
- Agent processes ↔ the UI layer
- Multiple concurrent agents ↔ a shared coordination bus

`remoteBridgeCore.ts` is specifically the core of the remote mode — the component that implements bidirectional messaging when an agent runs on a remote host.

The server subsystem (`server.json`) works in tandem:
- `createDirectConnectSession.ts` — creates a direct-connect session
- `directConnectManager.ts` — manages active direct-connect sessions
- `types.ts` — shared type definitions

The remote subsystem (`remote.json`) handles session management at the network level:
- `RemoteSessionManager.ts` — manages remote session lifecycle
- `SessionsWebSocket.ts` — WebSocket-based session transport
- `remotePermissionBridge.ts` — bridges permission decisions across process boundaries
- `sdkMessageAdapter.ts` — adapts SDK messages to the remote session format

---

## 23. The Services Layer

The `services` subsystem has **130 modules** — the largest named subsystem. Key agent-related services:

### `AgentSummary`
**Source:** `services/AgentSummary/agentSummary.ts`

A service that summarises the activity and output of agent runs. Likely used to produce structured post-run reports for logging, debugging, or user display.

### `SessionMemory`
Session memory service — persists agent memory across sessions. Distinct from the in-turn `agentMemory` and `agentMemorySnapshot` modules (which are ephemeral), this is the **durable memory layer** that allows an agent to remember things from previous sessions.

### `PromptSuggestion`
A service that suggests prompts to the user based on context — a UX feature that makes the agent system more accessible by predicting what the user might want to ask next.

### Analytics services
- `analytics/Datadog` — sends telemetry to Datadog
- `analytics/firstPartyEventLogger` — logs first-party events (for internal analytics)

These confirm that production deployments of the harness report metrics to external observability platforms.

### `MagicDocs`
A documentation service integrated with the agent system.

### API services
- `api/adminRequests` — admin-level API requests
- `api/bootstrap` — bootstrap API calls
- `api/claude` — direct Claude API calls
- `api/client` — API client setup
- `api/errors` — API error handling

---

## 24. Skills as Agent Extensions

The `skills` subsystem has **20 modules**. Skills are slash-command-style extensions that augment the agent's capabilities without being part of the core tool suite.

Full skill inventory from `src/reference_data/subsystems/skills.json`:

| Skill | Purpose |
|-------|---------|
| `batch` | Execute a set of operations in batch |
| `claudeApi` | Invoke the Claude API directly from a skill |
| `claudeApiContent` | Handle Claude API content streaming |
| `claudeInChrome` | Browser automation via Chrome extension |
| `debug` | Debug utilities for agent development |
| `keybindings` | Customise keyboard shortcuts |
| `loop` | Run a prompt/command on a recurring interval |
| `loremIpsum` | Generate placeholder text |
| `remember` | Persist information to agent memory |
| `scheduleRemoteAgents` | Schedule agents to run on a cron schedule |
| `simplify` | Review and simplify recently changed code |
| `skillify` | Create new skills from existing workflows |
| `stuck` | Rescue an agent that is stuck or looping |
| `updateConfig` | Update the harness configuration |
| `verify` | Verify that changes meet requirements |
| `verifyContent` | Verify content against a specification |

Key observations:
- `scheduleRemoteAgents` — skills can trigger and schedule remote agent execution (not just local)
- `loop` — recursive agent execution: a skill that runs another skill/command on a timer
- `remember` — direct skill-level memory write: agents can explicitly persist information
- `stuck` / `verify` / `verifyContent` — meta-agents: agents that monitor and correct other agents
- `skillify` — agents can **create new skills**, enabling self-extending behaviour

Skills are loaded via `skill_init` (part of deferred init, `trusted=True` required) and surface as skill-like commands in the `CommandGraph`.

---

## 25. Hooks System

The `hooks` subsystem has **104 modules**. Hooks are lifecycle callbacks that fire on specific events in the agent session.

Key hook categories from `src/reference_data/subsystems/hooks.json`:

### Tool permission hooks
These fire when an agent requests permission to use a tool:
- `toolPermission/coordinator` — permission check in coordinator mode
- `toolPermission/interactive` — permission check with human-in-the-loop approval
- `toolPermission/swarmWorker` — permission check for swarm worker agents

### Notification hooks (`notifs/`)
These fire at specific system events and deliver notifications to the user:
- `autoMode` — fires when auto-mode is toggled
- `deprecation` — fires when a deprecated feature is used
- `fastMode` — fires when fast mode is enabled/disabled
- `lspInitialization` — fires when LSP (Language Server Protocol) initialises
- `mcpConnectivity` — fires when MCP server connectivity changes
- `modelMigration` — fires when the model version changes
- `pluginUpdates` — fires when plugin updates are available
- `rateLimiting` — fires when API rate limits are hit
- `startup` — fires at session startup
- `teammateShutdown` — fires when a teammate agent shuts down

The `teammateShutdown` notification hook is particularly revealing: it confirms that the harness supports **named teammate agents** that can be running and that can shut down during a session — a multi-agent topology where other agents are treated as addressable collaborators.

---

## 26. Application State for Multi-Agent Views

The `state` subsystem has 6 modules:

| Module | Purpose |
|--------|---------|
| `AppState.tsx` | Root application state component |
| `AppStateStore.ts` | State store (likely Redux or Zustand) |
| `onChangeAppState.ts` | State change subscription handler |
| `selectors.ts` | State selectors |
| `store.ts` | Store initialisation |
| `teammateViewHelpers.ts` | Helper utilities for rendering teammate (multi-agent) views |

`teammateViewHelpers.ts` is the state-layer counterpart to `agentColorManager.ts` — it handles the data/logic side of displaying multiple agents in the UI, while the color manager handles the visual identity side.

---

## 27. Complete Tool Inventory: Agent-Related Tools

All agent-related tools from `src/reference_data/tools_snapshot.json`, organised by subsystem:

### AgentTool subsystem (18 tools)
```
AgentTool              tools/AgentTool/AgentTool.tsx
UI                     tools/AgentTool/UI.tsx
agentColorManager      tools/AgentTool/agentColorManager.ts
agentDisplay           tools/AgentTool/agentDisplay.ts
agentMemory            tools/AgentTool/agentMemory.ts
agentMemorySnapshot    tools/AgentTool/agentMemorySnapshot.ts
agentToolUtils         tools/AgentTool/agentToolUtils.ts
builtInAgents          tools/AgentTool/builtInAgents.ts
constants              tools/AgentTool/constants.ts
forkSubagent           tools/AgentTool/forkSubagent.ts
loadAgentsDir          tools/AgentTool/loadAgentsDir.ts
prompt                 tools/AgentTool/prompt.ts
resumeAgent            tools/AgentTool/resumeAgent.ts
runAgent               tools/AgentTool/runAgent.ts
claudeCodeGuideAgent   tools/AgentTool/built-in/claudeCodeGuideAgent.ts
exploreAgent           tools/AgentTool/built-in/exploreAgent.ts
generalPurposeAgent    tools/AgentTool/built-in/generalPurposeAgent.ts
planAgent              tools/AgentTool/built-in/planAgent.ts
statuslineSetup        tools/AgentTool/built-in/statuslineSetup.ts
verificationAgent      tools/AgentTool/built-in/verificationAgent.ts
```

### Task management tools (18 tools)
```
TaskCreateTool    tools/TaskCreateTool/TaskCreateTool.ts
                  tools/TaskCreateTool/constants.ts
                  tools/TaskCreateTool/prompt.ts
TaskGetTool       tools/TaskGetTool/TaskGetTool.ts
                  tools/TaskGetTool/constants.ts
                  tools/TaskGetTool/prompt.ts
TaskListTool      tools/TaskListTool/TaskListTool.ts
                  tools/TaskListTool/constants.ts
                  tools/TaskListTool/prompt.ts
TaskUpdateTool    tools/TaskUpdateTool/TaskUpdateTool.ts
                  tools/TaskUpdateTool/constants.ts
                  tools/TaskUpdateTool/prompt.ts
TaskOutputTool    tools/TaskOutputTool/TaskOutputTool.tsx
                  tools/TaskOutputTool/constants.ts
TaskStopTool      tools/TaskStopTool/TaskStopTool.ts
                  tools/TaskStopTool/UI.tsx
                  tools/TaskStopTool/prompt.ts
```

### Team and messaging tools (12 tools)
```
SendMessageTool   tools/SendMessageTool/SendMessageTool.ts
                  tools/SendMessageTool/UI.tsx
                  tools/SendMessageTool/constants.ts
                  tools/SendMessageTool/prompt.ts
TeamCreateTool    tools/TeamCreateTool/TeamCreateTool.ts
                  tools/TeamCreateTool/UI.tsx
                  tools/TeamCreateTool/constants.ts
                  tools/TeamCreateTool/prompt.ts
TeamDeleteTool    tools/TeamDeleteTool/TeamDeleteTool.ts
                  tools/TeamDeleteTool/UI.tsx
                  tools/TeamDeleteTool/constants.ts
                  tools/TeamDeleteTool/prompt.ts
```

### Multi-agent shared utilities (1 tool)
```
spawnMultiAgent   tools/shared/spawnMultiAgent.ts
```

---

## 28. Complete Command Inventory: Agent-Related Commands

From `src/reference_data/commands_snapshot.json`:

### Agent commands
```
agents    commands/agents/agents.tsx    (UI component)
agents    commands/agents/index.ts      (CLI router)
```

### Task commands
```
tasks     commands/tasks/tasks.tsx      (UI component)
tasks     commands/tasks/index.ts       (CLI router)
```

The duplication (same name, two files) is the standard pattern: `index.ts` is the programmatic entry point; the `.tsx` file is the React component rendering the command's UI in the terminal.

---

## 29. Current Agent Implementation State

This section describes what is actually implemented in the Python port as of the current codebase, distinct from the TypeScript architecture described elsewhere in this document.

### What works now

Agent and team tools are implemented as **honest stubs**: they record intent in the in-memory store and return structured results immediately, but do not spawn real LLM sub-processes.

#### Agent creation and ID assignment

`AgentTool`, `runAgent`, and `forkSubagent` all create `AgentRecord` entries in `stores._agents` via `stores.create_agent()` and return a JSON response including `agent_id`.

```bash
python3 -m src.main exec-tool AgentTool '{"prompt": "Summarise the repo"}'
# Output: {"agent_id": "agt-a1b2c3", "status": "pending", "prompt": "Summarise the repo"}

python3 -m src.main exec-tool forkSubagent '{"prompt": "Run tests", "parent_agent_id": "agt-a1b2c3"}'
# Output: {"agent_id": "agt-d4e5f6", "parent_id": "agt-a1b2c3", "status": "pending"}
```

`runAgent` additionally calls `stores.complete_agent()`, marking the record with `status="completed"` and a synthetic result string.

#### Parallel agent spawning

`spawnMultiAgent` accepts a list of agent specs and creates one `AgentRecord` per prompt. All records are created in the same process call and the full list of agent IDs is returned.

```bash
python3 -m src.main exec-tool spawnMultiAgent \
  '{"agents": [{"prompt": "Task A"}, {"prompt": "Task B"}]}'
# Output: {"spawned": 2, "agent_ids": ["agt-...", "agt-..."], "agents": [...]}
```

#### Team management

`TeamCreateTool` and `TeamDeleteTool` manage `TeamRecord` entries in `stores._teams`.

```bash
python3 -m src.main exec-tool TeamCreateTool '{"name": "search-team"}'
# Output: {"team_id": "tm-...", "name": "search-team"}

python3 -m src.main exec-tool TeamDeleteTool '{"team_id": "tm-..."}'
# Output: {"deleted": true, "team_id": "tm-..."}
```

#### Message routing

`SendMessageTool` logs a message against a named team and returns a delivery confirmation. Messages are stored in-memory and visible within the same process.

```bash
python3 -m src.main exec-tool SendMessageTool '{"team": "search-team", "message": "task complete"}'
# Output: {"delivered": true, "team": "search-team", "message": "task complete"}
```

### What does not work

| Capability | Status | Notes |
|------------|--------|-------|
| Real LLM sub-process spawning | Not implemented | `AgentRecord.status` is set to `"pending"` or `"completed"` without any actual API call |
| Actual LLM inference in subagents | Not implemented | `result` field in `runAgent` is a synthetic string, not real model output |
| Memory persistence across restarts | Not implemented | All `AgentRecord`, `TeamRecord`, and message data lives in `stores._agents` / `stores._teams` which are plain dicts reset on every process start |
| `resumeAgent` | Not implemented | No handler registered in `TOOL_DISPATCH` |
| `agentMemory` / `agentMemorySnapshot` | Not implemented | No handlers; TypeScript-only at this stage |
| Concurrent multi-agent execution | Not implemented | `spawnMultiAgent` creates records sequentially in a single thread |

To extend agent tools with real LLM behaviour, integrate an Anthropic API client in `src/tool_implementations/agent_tools.py` and replace the `stores.complete_agent()` stub with an actual model call.

---

## 30. Architectural Summary

### The four layers of the agent harness

```
┌───────────────────────────────────────────────────────┐
│  LAYER 4: EXTENSION LAYER                             │
│  Skills (20)   Plugins (2)   Custom agents (loadAgentsDir) │
│  Hooks (104 lifecycle callbacks)                       │
└───────────────────────┬───────────────────────────────┘
                        │
┌───────────────────────▼───────────────────────────────┐
│  LAYER 3: AGENT TOOL LAYER                            │
│  AgentTool (18 modules)                               │
│  ├── Built-in agents (6): explore, plan, general,     │
│  │   claudeCodeGuide, verification, statuslineSetup   │
│  ├── Lifecycle: runAgent, forkSubagent, resumeAgent   │
│  ├── Memory: agentMemory, agentMemorySnapshot         │
│  └── Display: agentDisplay, agentColorManager         │
│                                                       │
│  Task Tools (6): Create, Get, List, Update, Output, Stop │
│  Team Tools (3): TeamCreate, TeamDelete, SendMessage  │
│  Multi-agent: spawnMultiAgent                         │
└───────────────────────┬───────────────────────────────┘
                        │
┌───────────────────────▼───────────────────────────────┐
│  LAYER 2: RUNTIME LAYER                               │
│  PortRuntime: route_prompt, bootstrap_session,        │
│               run_turn_loop                           │
│  QueryEnginePort: submit_message, stream_submit,      │
│                   persist_session                     │
│  CoordinatorMode: coordinator ↔ swarm worker          │
│  PermissionSystem: ToolPermissionContext + bash gate  │
│  SessionStore: .port_sessions/ JSON persistence       │
│  TranscriptStore: compaction + replay                 │
└───────────────────────┬───────────────────────────────┘
                        │
┌───────────────────────▼───────────────────────────────┐
│  LAYER 1: INFRASTRUCTURE LAYER                        │
│  Bootstrap (7 stages): prefetch → trust gate →        │
│                         load → deferred init →        │
│                         mode routing → submit loop    │
│  Bridge (31 modules): IPC, remote bridge, WebSocket   │
│  Services (130 modules): AgentSummary, SessionMemory, │
│                           analytics, API client       │
│  Remote modes: local / remote / SSH / teleport /      │
│                direct-connect / deep-link             │
└───────────────────────────────────────────────────────┘
```

### Key design principles

1. **Registry-driven dispatch** — Commands and tools are data (JSON), not hardcoded logic. The runtime routes to them by name. Adding a new agent capability means adding an entry to the registry.

2. **Trust-gated extensibility** — Extensions (plugins, skills, MCP tools, hooks) only load in trusted sessions. Untrusted sessions run with a minimal, safe subset.

3. **Role-differentiated permission** — Coordinator and swarm worker agents operate under different permission regimes. The hooks system enforces role-appropriate access to tools.

4. **Hierarchical agent delegation** — `forkSubagent` enables parent → child delegation. `spawnMultiAgent` enables peer-level parallel execution. `TeamCreate`/`SendMessage` enables named-group coordination.

5. **Memory at three levels** — Ephemeral in-turn memory (`agentMemory`), session snapshots (`agentMemorySnapshot`), and durable cross-session memory (`SessionMemory` service + `remember` skill).

6. **Event-streaming protocol** — The `stream_submit_message` event sequence mirrors the Anthropic API streaming format, allowing the harness to act as a transparent streaming proxy between the user and the model.

7. **Budget-aware execution** — Every turn tracks token consumption. The loop stops cleanly when the budget is exhausted rather than running open-ended.

8. **Resumable sessions** — Sessions are always persisted. Any agent session can be resumed exactly from where it left off.

9. **Distributed execution** — Remote, SSH, and Teleport modes allow agents to run on remote hosts, with the bridge layer handling bidirectional communication.

10. **Self-extending capability** — The `skillify` skill allows agents to create new skills. Combined with `loadAgentsDir`, the system can incorporate new capabilities at runtime without redeployment.
