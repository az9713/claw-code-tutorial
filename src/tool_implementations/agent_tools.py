from __future__ import annotations

import dataclasses
import json

from .. import stores


def handle_agent_tool(payload: str) -> str:
    try:
        params = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError:
        params = {"input": payload}

    prompt = params.get("prompt", "")
    if not prompt:
        return "Error: prompt is required"

    agent = stores.create_agent(prompt)
    return json.dumps({
        "agent_id": agent.agent_id,
        "status": agent.status,
        "prompt": agent.prompt,
    })


def handle_run_agent(payload: str) -> str:
    try:
        params = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError:
        params = {"input": payload}

    prompt = params.get("prompt", "")
    if not prompt:
        return "Error: prompt is required"

    agent = stores.create_agent(prompt)
    result_text = f"Agent completed: {prompt[:50]}"
    completed = stores.complete_agent(agent.agent_id, result_text)
    if completed is None:
        completed = agent

    return json.dumps({
        "agent_id": completed.agent_id,
        "status": completed.status,
        "prompt": completed.prompt,
        "result": completed.result,
    })


def handle_fork_subagent(payload: str) -> str:
    try:
        params = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError:
        params = {"input": payload}

    prompt = params.get("prompt", "")
    if not prompt:
        return "Error: prompt is required"

    parent_agent_id = params.get("parent_agent_id", "")

    agent = stores.create_agent(prompt, parent_id=parent_agent_id)
    return json.dumps({
        "agent_id": agent.agent_id,
        "parent_id": agent.parent_id,
        "status": agent.status,
    })


def handle_spawn_multi_agent(payload: str) -> str:
    try:
        params = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError:
        params = {"input": payload}

    agents_spec = params.get("agents", [])
    if not isinstance(agents_spec, list):
        return "Error: agents must be a list"

    spawned_agents = []
    agent_ids = []

    for spec in agents_spec:
        prompt = spec.get("prompt", "") if isinstance(spec, dict) else ""
        if not prompt:
            continue
        agent = stores.create_agent(prompt)
        agent_ids.append(agent.agent_id)
        spawned_agents.append({
            "agent_id": agent.agent_id,
            "prompt": agent.prompt,
            "status": agent.status,
        })

    return json.dumps({
        "spawned": len(spawned_agents),
        "agent_ids": agent_ids,
        "agents": spawned_agents,
    })
