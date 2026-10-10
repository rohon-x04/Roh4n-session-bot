"""
All exporters below take the SAME underlying MTProto auth_key (obtained
once via a real login) and re-encode it for different client libraries.
No separate login/auth happens per format — this is pure re-serialization.

mtcute is intentionally NOT implemented: its session format isn't
something to hand-roll from memory for a credential-bearing string.
Shipping a guessed encoding here would risk a string that looks valid
but silently fails to authenticate, which is worse than not offering it.
"""

import struct
import base64
import json

# Well-known production Telegram DC addresses (public, documented by
# Telethon/MadelineProto/etc.) — needed only to build Telethon/GramJS
# StringSessions, which encode a DC ip:port alongside the auth key.
DC_IPV4 = {
    1: "149.154.175.53", 2: "149.154.167.51", 3: "149.154.175.100",
    4: "149.154.167.91", 5: "91.108.56.151",
}
DC_IPV6 = {
    1: "2001:0b28:f23d:f001:0000:0000:0000:000a",
    2: "2001:067c:04e8:f002:0000:0000:0000:000a",
    3: "2001:0b28:f23d:f003:0000:0000:0000:000a",
    4: "2001:067c:04e8:f004:0000:0000:0000:000a",
    5: "2001:0b28:f23f:f005:0000:0000:0000:000a",
}
DC_PORT = 443


def pyrogram_v2(dc_id, api_id, test_mode, auth_key, user_id, is_bot) -> str:
    """Native Pyrogram >=2.0 format. Mirrors Client.export_session_string()."""
    packed = struct.pack(">BI?256sQ?", dc_id, api_id, test_mode, auth_key, user_id, is_bot)
    return base64.urlsafe_b64encode(packed).decode().rstrip("=")


def pyrogram_v1(dc_id, test_mode, auth_key, user_id, is_bot) -> str:
    """Legacy pre-2.0 Pyrogram format: no api_id field."""
    packed = struct.pack(">B?256sQ?", dc_id, test_mode, auth_key, user_id, is_bot)
    return base64.urlsafe_b64encode(packed).decode().rstrip("=")


def telethon_string_session(dc_id, auth_key, use_ipv6: bool) -> str:
    """
    Delegates to Telethon's own StringSession implementation rather than
    hand-encoding, so the output is guaranteed to match what Telethon
    (and GramJS, which shares the format) actually expects.
    """
    from telethon.sessions import StringSession
    from telethon.crypto import AuthKey

    ip = DC_IPV6[dc_id] if use_ipv6 else DC_IPV4[dc_id]
    ss = StringSession()
    ss.set_dc(dc_id, ip, DC_PORT)
    ss.auth_key = AuthKey(data=auth_key)
    return ss.save()


def raw_mtproto(dc_id, auth_key, user_id, is_bot, test_mode) -> str:
    return json.dumps({
        "dc_id": dc_id,
        "auth_key_hex": auth_key.hex(),
        "user_id": user_id,
        "is_bot": is_bot,
        "test_mode": test_mode,
    }, indent=2)


def build_all(dc_id, api_id, test_mode, auth_key, user_id, is_bot) -> dict:
    """Returns {label: string_or_None}. None = failed to build (library/data issue)."""
    out = {}

    out["Pyrogram v2 (latest)"] = pyrogram_v2(dc_id, api_id, test_mode, auth_key, user_id, is_bot)
    out["Pyrogram v1 (legacy)"] = pyrogram_v1(dc_id, test_mode, auth_key, user_id, is_bot)
    out["Hydrogram"] = out["Pyrogram v2 (latest)"]  # fork, same wire format
    out["Kurigram"] = out["Pyrogram v2 (latest)"]   # fork, same wire format

    try:
        out["Telethon (IPv4)"] = telethon_string_session(dc_id, auth_key, use_ipv6=False)
        out["Telethon (IPv6)"] = telethon_string_session(dc_id, auth_key, use_ipv6=True)
        out["GramJS"] = out["Telethon (IPv4)"]  # same StringSession format
    except ImportError:
        out["Telethon (IPv4)"] = None
        out["Telethon (IPv6)"] = None
        out["GramJS"] = None

    out["Raw MTProto"] = raw_mtproto(dc_id, auth_key, user_id, is_bot, test_mode)
    out["mtcute"] = None  # not implemented — see module docstring

    return out
