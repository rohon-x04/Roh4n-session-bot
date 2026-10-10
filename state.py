"""
Pure in-memory, per-user conversation state for the login flow.

CRITICAL SAFETY PROPERTY: nothing in this module ever touches disk,
a database, or a log line. Entries vanish on process restart and are
force-expired after FLOW_TIMEOUT seconds even if the user goes idle.
Do not add persistence here.
"""

import time
import asyncio
from config import FLOW_TIMEOUT, COOLDOWN_SECONDS

# user_id -> dict(step, client, phone, phone_code_hash, created_at)
_sessions: dict[int, dict] = {}

# user_id -> last attempt timestamp (for cooldown only, no content stored)
_last_attempt: dict[int, float] = {}


def set_custom_api(user_id: int, api_id: int, api_hash: str):
    """Stash a user-supplied api_id/api_hash in memory only, pending login start."""
    _sessions[user_id] = {
        "step": "awaiting_phone",
        "client": None,
        "phone": None,
        "phone_code_hash": None,
        "api_id": api_id,
        "api_hash": api_hash,
        "created_at": time.time(),
    }


def get_custom_api(user_id: int) -> tuple[int, str] | None:
    s = _sessions.get(user_id)
    if s and s.get("api_id") and s.get("api_hash"):
        return s["api_id"], s["api_hash"]
    return None


def start_flow(user_id: int, client, phone: str, phone_code_hash: str):
    prev = _sessions.get(user_id, {})
    _sessions[user_id] = {
        "step": "awaiting_code",
        "client": client,
        "phone": phone,
        "phone_code_hash": phone_code_hash,
        "api_id": prev.get("api_id"),
        "api_hash": prev.get("api_hash"),
        "fmt": prev.get("fmt"),
        "created_at": time.time(),
    }


def set_format(user_id: int, fmt: str):
    if user_id in _sessions:
        _sessions[user_id]["fmt"] = fmt


def get(user_id: int) -> dict | None:
    s = _sessions.get(user_id)
    if s and time.time() - s["created_at"] > FLOW_TIMEOUT:
        # Expired: wipe it immediately.
        asyncio.create_task(_safe_disconnect(s.get("client")))
        _sessions.pop(user_id, None)
        return None
    return s


def set_step(user_id: int, step: str):
    if user_id in _sessions:
        _sessions[user_id]["step"] = step


async def clear(user_id: int):
    s = _sessions.pop(user_id, None)
    if s:
        await _safe_disconnect(s.get("client"))


async def _safe_disconnect(client):
    if client is None:
        return
    try:
        if client.is_connected:
            await client.disconnect()
    except Exception:
        pass


def check_cooldown(user_id: int) -> float:
    """Returns remaining cooldown seconds (0 if the user may proceed)."""
    now = time.time()
    last = _last_attempt.get(user_id, 0)
    remaining = COOLDOWN_SECONDS - (now - last)
    return max(0.0, remaining)


def mark_attempt(user_id: int):
    _last_attempt[user_id] = time.time()
