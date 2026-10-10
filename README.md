# ʀᴏʜ፝֟͝ꫝɴ ꭙ ꜱᴇꜱꜱɪᴏɴ — Premium Telegram String Session Generator

## What it does
Walks a user through phone → login code → (2FA if needed) → a Pyrogram
session string for their own account, with a premium-styled inline UI.

## Safety design (do not remove these when extending the bot)
- `in_memory=True` on every temp `Client` — never writes a `.session`
  file to disk.
- `state.py` holds phone/code/password/session **only in RAM**, keyed
  by user id, auto-expired after `FLOW_TIMEOUT` seconds.
- The session string is sent to the user **once** and then the
  in-memory client/credentials are wiped (`state.clear`), win or lose.
- The result message self-destructs after 60s as a best-effort nudge
  (not a security guarantee — tell users to save it immediately).
- Nothing is ever printed/logged containing phone numbers, codes,
  passwords, or session strings.
- Per-user cooldown (`COOLDOWN_SECONDS`) after a successful generation
  to slow down abuse/brute-forcing.

**If you modify this bot: never add a database write, a log line, or
a "forward to admin/owner" step for the phone/code/password/session
values.** That would turn this from a legitimate self-service tool
into a credential-harvesting bot.

## Multi-format exports (`formats.py`)
All formats are re-encodings of the *same* auth_key obtained from one
real login — no extra auth happens per format.

| Format | Status |
|---|---|
| Pyrogram v2 | Native, from Pyrogram itself |
| Pyrogram v1 (legacy) | Hand-encoded struct layout, matches documented pre-2.0 format |
| Hydrogram / Kurigram | Same as Pyrogram v2 (forks kept the wire format) |
| Telethon IPv4 / IPv6 | Built via Telethon's own `StringSession`/`AuthKey` classes |
| GramJS | Same string as Telethon (shared StringSession spec) |
| Raw MTProto | dc_id + auth_key hex + user_id/is_bot, plain JSON |
| mtcute | **Not implemented** — format wasn't verified, so it's refused rather than guessed |

⚠️ **Verify before shipping to real users:** this environment couldn't
install/run Telethon to confirm `StringSession.set_dc()` and
`AuthKey(data=...)` behave exactly as written in `formats.py`. Test a
Telethon/GramJS string end-to-end (actually log in with it) before
trusting it in production — everything else compiles clean, but
compiling isn't the same as a confirmed working session.

## Setup

1. Get `API_ID` / `API_HASH` from https://my.telegram.org
2. Create a bot with [@BotFather](https://t.me/BotFather), get `BOT_TOKEN`
3. Set `BOT_TOKEN`'s name/about/profile picture via BotFather to match
   the "ʀᴏʜ፝֟͝ꫝɴ ꭙ ꜱᴇꜱꜱɪᴏɴ" branding (bots can't self-rename via code)

## Deploy on Render (free web service)

1. Push this folder to a GitHub repo
2. Render dashboard → New → Web Service → connect the repo
3. Environment: Python 3
4. Build command: `pip install -r requirements.txt`
5. Start command: `python main.py` (already in `Procfile`)
6. Add environment variables: `API_ID`, `API_HASH`, `BOT_TOKEN`
   (Render auto-sets `PORT`, no action needed there)
7. Deploy — Render's health check hits `/`, which the bot's own tiny
   aiohttp server answers, so the free instance stays up correctly.

## Local run

```bash
pip install -r requirements.txt
export API_ID=... API_HASH=... BOT_TOKEN=...
python main.py
```

## User flow
1. `/start` → disclosure + choice: default API creds or user's own
   (`/setapi`-style button → prompts for `API_ID API_HASH`)
2. Enter phone number
3. Enter the login code Telegram texts them
4. Enter 2FA password if their account has one
5. Receive the session string once, bot forgets everything
