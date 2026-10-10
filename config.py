import os

# ── Required environment variables (set these in Render's dashboard, never in code) ──
API_ID = int(os.environ["API_ID"])          # your api_id from my.telegram.org
API_HASH = os.environ["API_HASH"]           # your api_hash from my.telegram.org
BOT_TOKEN = os.environ["BOT_TOKEN"]         # token from @BotFather

# Optional
PORT = int(os.environ.get("PORT") or 8080)  # Render injects PORT automatically
OWNER_ID = int(os.environ.get("OWNER_ID", 0))  # used ONLY for /stats-style bot-usage counts, never for session content

# How long (seconds) a user has to complete the phone -> code -> (2FA) flow
# before their in-memory session attempt is discarded.
FLOW_TIMEOUT = 300

# Per-user cooldown between login attempts, to slow down brute-force / spam abuse.
COOLDOWN_SECONDS = 60
