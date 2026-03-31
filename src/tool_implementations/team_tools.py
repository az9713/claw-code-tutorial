from __future__ import annotations

import dataclasses
import json

from .. import stores


def handle_team_create(payload: str) -> str:
    try:
        params = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError:
        params = {"input": payload}

    name = params.get("name", "")
    if not name:
        return "Error: name is required"

    members = params.get("members", [])
    if not isinstance(members, list):
        return "Error: members must be a list"

    team = stores.create_team(name, members)
    return json.dumps({
        "team_id": team.team_id,
        "name": team.name,
        "member_names": list(team.member_names),
    })


def handle_team_delete(payload: str) -> str:
    try:
        params = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError:
        params = {"input": payload}

    team_id = params.get("team_id", "")
    if not team_id:
        return "Error: team_id is required"

    deleted = stores.delete_team(team_id)
    if deleted:
        return f"Team {team_id} deleted."
    return f"Team not found: {team_id}"


def handle_send_message(payload: str) -> str:
    try:
        params = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError:
        params = {"input": payload}

    team_id = params.get("team_id", "")
    member = params.get("member", "")
    message = params.get("message", "")

    if not team_id:
        return "Error: team_id is required"
    if not member:
        return "Error: member is required"
    if not message:
        return "Error: message is required"

    team = stores.get_team(team_id)
    if team is None:
        return f"Error: Team not found: {team_id}"

    stores.create_agent(f"Message to {member}: {message}")
    return f"Message delivered to {member} in team {team_id}."
