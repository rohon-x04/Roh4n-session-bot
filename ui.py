from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_DISPLAY_NAME = "ʀᴏʜ፝֟͝ꫝɴ ꭙ ꜱᴇꜱꜱɪᴏɴ"

WELCOME = f"""
✨ <b>{BOT_DISPLAY_NAME}</b> ✨
<i>Premium Pyrogram String Session Generator</i>

┌─「 ⚠️ <b>READ BEFORE YOU CONTINUE</b> 」
│
│ A session string is a <b>full login key</b> to your
│ Telegram account — not a password reset, not a
│ one-time code. Anyone who has it can read your
│ chats, send messages as you, and access your
│ account without needing your phone again.
│
│ • This bot does <b>not</b> store, log, or forward your
│   phone number, code, 2FA password, or the final
│   session string anywhere. It is generated and
│   sent to you once, then wiped from memory.
│ • <b>Never</b> share your session string with anyone —
│   including bot admins, "support", or giveaways.
│ • Use it only with code/bots you trust and control.
│
└──────────────────────────────

Choose how you'd like to proceed 👇
"""

def welcome_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Generate Session (default API)", callback_data="go_default")],
        [InlineKeyboardButton("🛠️ Use my own API ID / Hash", callback_data="go_custom")],
        [InlineKeyboardButton("ℹ️ What is a session string?", callback_data="info")],
    ])

FORMAT_LABELS = {
    "fmt_pyro2": "Pyrogram v2 (latest)",
    "fmt_pyro1": "Pyrogram v1 (legacy)",
    "fmt_tel4": "Telethon (IPv4)",
    "fmt_tel6": "Telethon (IPv6)",
    "fmt_gramjs": "GramJS",
    "fmt_mtcute": "mtcute",
    "fmt_hydro": "Hydrogram",
    "fmt_kuri": "Kurigram",
    "fmt_raw": "Raw MTProto",
    "fmt_all": "ALL FORMATS (simultaneous)",
}

ASK_FORMAT = "🧬 <b>Choose a session format:</b>"

def format_keyboard():
    rows = [
        [InlineKeyboardButton("Pyrogram v2 · Latest", callback_data="fmt_pyro2"),
         InlineKeyboardButton("Pyrogram v1 · Legacy", callback_data="fmt_pyro1")],
        [InlineKeyboardButton("Telethon IPv4", callback_data="fmt_tel4"),
         InlineKeyboardButton("Telethon IPv6", callback_data="fmt_tel6")],
        [InlineKeyboardButton("GramJS", callback_data="fmt_gramjs"),
         InlineKeyboardButton("mtcute ⚠️", callback_data="fmt_mtcute")],
        [InlineKeyboardButton("Hydrogram", callback_data="fmt_hydro"),
         InlineKeyboardButton("Kurigram", callback_data="fmt_kuri")],
        [InlineKeyboardButton("Raw MTProto", callback_data="fmt_raw")],
        [InlineKeyboardButton("✨ ALL FORMATS (Recommended)", callback_data="fmt_all")],
    ]
    return InlineKeyboardMarkup(rows)

INFO_TEXT = """
ℹ️ <b>What is a Pyrogram/Telethon session string?</b>

It's an encoded blob that lets a script log in as your
Telegram account instantly — no phone number, no SMS
code, no 2FA needed again. It's commonly used to run
userbots or automation tools under your own account.

<b>Treat it like a password — because it's stronger than one.</b>
"""

ASK_PHONE = (
    "📱 Send your phone number in <b>international format</b>, e.g:\n"
    "<code>+15551234567</code>\n\n"
    "You can cancel anytime with /cancel."
)

ASK_CUSTOM_API = (
    "🛠️ Send your own <b>API ID</b> and <b>API HASH</b> from "
    "<a href='https://my.telegram.org'>my.telegram.org</a>, "
    "separated by a space, e.g:\n"
    "<code>123456 abcdef1234567890abcdef1234567890</code>"
)

ASK_CODE = (
    "💬 Telegram just sent a login code to <b>{phone}</b>.\n\n"
    "Enter it here. If it arrives as <code>1 2 3 4 5</code>, type it "
    "<b>without spaces</b>: <code>12345</code>\n\n"
    "⚠️ If someone other than this bot asks you for this code, it's a scam — "
    "never share it anywhere else."
)

ASK_PASSWORD = (
    "🔒 Your account has <b>Two-Step Verification</b> enabled.\n"
    "Send your 2FA password to finish."
)

def session_result(session_string: str) -> str:
    return (
        "✅ <b>Session generated successfully.</b>\n\n"
        f"<code>{session_string}</code>\n\n"
        "⚠️ This message is sensitive — forward it to <b>nowhere</b>, "
        "store it somewhere private, and delete this chat message once saved.\n"
        "This bot keeps <b>no copy</b> of it."
    )

def session_result_multi(results: dict) -> list[str]:
    """
    Splits the "ALL FORMATS" output into one message per format so none
    of them get truncated and each is independently easy to copy/delete.
    Unavailable formats (None) are called out rather than silently omitted.
    """
    header = (
        "✅ <b>All available formats generated.</b>\n"
        "Same underlying login, re-encoded per library. Save these somewhere "
        "private, then delete these messages — nothing is kept here.\n"
    )
    chunks = [header]
    for label, value in results.items():
        if value is None:
            chunks.append(f"⚠️ <b>{label}</b>\nNot generated (unsupported/unavailable in this bot).")
        else:
            chunks.append(f"🔹 <b>{label}</b>\n<code>{value}</code>")
    return chunks

CANCELLED = "❌ Flow cancelled. Nothing was saved."
TIMED_OUT = "⏱️ You took too long — the login attempt expired for your safety. Use /start to try again."
COOLDOWN = "🧊 Please wait {s}s before trying again (abuse protection)."
GENERIC_ERROR = "⚠️ Something went wrong: {err}\n\nUse /start to try again."
