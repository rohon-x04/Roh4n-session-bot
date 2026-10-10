import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from pyrogram.errors import (
    PhoneNumberInvalid, PhoneCodeInvalid, PhoneCodeExpired,
    SessionPasswordNeeded, PasswordHashInvalid, FloodWait, ApiIdInvalid,
)

import config
import state
import ui
import formats

bot = Client(
    "session_bot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
)


@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(_, m: Message):
    await state.clear(m.from_user.id)
    await m.reply_text(ui.WELCOME, reply_markup=ui.welcome_keyboard(), disable_web_page_preview=True)


@bot.on_message(filters.command("cancel") & filters.private)
async def cancel_cmd(_, m: Message):
    await state.clear(m.from_user.id)
    await m.reply_text(ui.CANCELLED)


@bot.on_callback_query(filters.regex("^info$"))
async def info_cb(_, cq: CallbackQuery):
    await cq.answer()
    await cq.message.reply_text(ui.INFO_TEXT, disable_web_page_preview=True)


@bot.on_callback_query(filters.regex("^go_default$"))
async def go_default_cb(_, cq: CallbackQuery):
    await cq.answer()
    user_id = cq.from_user.id
    remaining = state.check_cooldown(user_id)
    if remaining > 0:
        await cq.message.reply_text(ui.COOLDOWN.format(s=int(remaining)))
        return
    await state.clear(user_id)
    state._sessions[user_id] = {
        "step": "awaiting_format", "client": None, "phone": None,
        "phone_code_hash": None, "api_id": None, "api_hash": None, "fmt": None,
        "created_at": __import__("time").time(),
    }
    await cq.message.reply_text(ui.ASK_FORMAT, reply_markup=ui.format_keyboard())


@bot.on_callback_query(filters.regex("^go_custom$"))
async def go_custom_cb(_, cq: CallbackQuery):
    await cq.answer()
    user_id = cq.from_user.id
    remaining = state.check_cooldown(user_id)
    if remaining > 0:
        await cq.message.reply_text(ui.COOLDOWN.format(s=int(remaining)))
        return
    await state.clear(user_id)
    state._sessions[user_id] = {
        "step": "awaiting_custom_api", "client": None, "phone": None,
        "phone_code_hash": None, "api_id": None, "api_hash": None, "fmt": None,
        "created_at": __import__("time").time(),
    }
    await cq.message.reply_text(ui.ASK_CUSTOM_API, disable_web_page_preview=True)


@bot.on_callback_query(filters.regex("^fmt_"))
async def format_cb(_, cq: CallbackQuery):
    await cq.answer()
    user_id = cq.from_user.id
    s = state.get(user_id)
    if not s or s["step"] != "awaiting_format":
        await cq.message.reply_text("⌛ That format menu expired. Use /start again.")
        return
    state.set_format(user_id, cq.data)  # e.g. "fmt_pyro2" or "fmt_all"
    state.set_step(user_id, "awaiting_phone")
    await cq.message.reply_text(
        f"Selected: <b>{ui.FORMAT_LABELS[cq.data]}</b>\n\n" + ui.ASK_PHONE,
        disable_web_page_preview=True,
    )


@bot.on_message(filters.private & filters.text & ~filters.command(["start", "cancel"]))
async def flow_text(_, m: Message):
    user_id = m.from_user.id
    s = state.get(user_id)
    if not s:
        return  # not mid-flow and not a recognized command; stay quiet

    step = s["step"]

    if step == "awaiting_custom_api":
        await _handle_custom_api(m, user_id)
    elif step == "awaiting_phone":
        await _handle_phone(m, user_id)
    elif step == "awaiting_code":
        await _handle_code(m, user_id, s)
    elif step == "awaiting_password":
        await _handle_password(m, user_id, s)


async def _handle_custom_api(m: Message, user_id: int):
    parts = m.text.strip().split()
    if len(parts) != 2 or not parts[0].isdigit():
        await m.reply_text("❌ Invalid format. Send: <code>API_ID API_HASH</code>")
        return
    api_id, api_hash = int(parts[0]), parts[1]
    state.set_custom_api(user_id, api_id, api_hash)
    state.set_step(user_id, "awaiting_format")
    await m.reply_text(ui.ASK_FORMAT, reply_markup=ui.format_keyboard())


async def _handle_phone(m: Message, user_id: int):
    phone = m.text.strip()
    custom = state.get_custom_api(user_id)
    api_id, api_hash = custom if custom else (config.API_ID, config.API_HASH)

    client = Client(
        f"tmp_{user_id}",
        api_id=api_id,
        api_hash=api_hash,
        in_memory=True,  # never writes a .session file to disk
    )
    try:
        await client.connect()
        sent = await client.send_code(phone)
        state.start_flow(user_id, client, phone, sent.phone_code_hash)
        await m.reply_text(ui.ASK_CODE.format(phone=phone))
    except ApiIdInvalid:
        await m.reply_text("❌ That API ID/HASH pair is invalid. Use /start to try again.")
        await state.clear(user_id)
    except PhoneNumberInvalid:
        await m.reply_text("❌ Invalid phone number. Use /start to try again.")
        await state.clear(user_id)
    except FloodWait as e:
        await m.reply_text(f"🧊 Telegram is rate-limiting this action. Try again in {e.value}s.")
        await state.clear(user_id)
    except Exception as e:
        await m.reply_text(ui.GENERIC_ERROR.format(err=type(e).__name__))
        await state.clear(user_id)


async def _handle_code(m: Message, user_id: int, s: dict):
    code = m.text.strip().replace(" ", "")
    client: Client = s["client"]
    try:
        await client.sign_in(s["phone"], s["phone_code_hash"], code)
        await _finish(m, user_id, client, s.get("fmt"))
    except SessionPasswordNeeded:
        state.set_step(user_id, "awaiting_password")
        await m.reply_text(ui.ASK_PASSWORD)
    except (PhoneCodeInvalid, PhoneCodeExpired):
        await m.reply_text("❌ Code invalid or expired. Use /start to try again.")
        await state.clear(user_id)
    except FloodWait as e:
        await m.reply_text(f"🧊 Rate-limited by Telegram. Try again in {e.value}s.")
        await state.clear(user_id)
    except Exception as e:
        await m.reply_text(ui.GENERIC_ERROR.format(err=type(e).__name__))
        await state.clear(user_id)


async def _handle_password(m: Message, user_id: int, s: dict):
    password = m.text
    client: Client = s["client"]
    try:
        await client.check_password(password)
        await _finish(m, user_id, client, s.get("fmt"))
    except PasswordHashInvalid:
        await m.reply_text("❌ Wrong 2FA password. Try again or /cancel.")
    except FloodWait as e:
        await m.reply_text(f"🧊 Rate-limited by Telegram. Try again in {e.value}s.")
        await state.clear(user_id)
    except Exception as e:
        await m.reply_text(ui.GENERIC_ERROR.format(err=type(e).__name__))
        await state.clear(user_id)


async def _finish(m: Message, user_id: int, client: Client, fmt: str | None):
    sent_messages = []
    try:
        # Pull the raw auth material once — everything below is just
        # re-encoding of this same material, no extra login/auth calls.
        dc_id = await client.storage.dc_id()
        api_id = client.api_id
        test_mode = await client.storage.test_mode()
        auth_key = await client.storage.auth_key()
        user_id_tg = await client.storage.user_id()
        is_bot = await client.storage.is_bot()

        state.mark_attempt(user_id)

        if fmt is None or fmt == "fmt_pyro2":
            value = formats.pyrogram_v2(dc_id, api_id, test_mode, auth_key, user_id_tg, is_bot)
            sent_messages.append(await m.reply_text(ui.session_result(value)))

        elif fmt == "fmt_all":
            results = formats.build_all(dc_id, api_id, test_mode, auth_key, user_id_tg, is_bot)
            for chunk in ui.session_result_multi(results):
                sent_messages.append(await m.reply_text(chunk))

        elif fmt == "fmt_mtcute":
            sent_messages.append(await m.reply_text(
                "⚠️ mtcute export isn't implemented in this bot — its session "
                "format wasn't available to verify, and a guessed encoding "
                "could silently fail to log in. All other formats are supported; "
                "use /start to pick one."
            ))

        else:
            all_results = formats.build_all(dc_id, api_id, test_mode, auth_key, user_id_tg, is_bot)
            label = ui.FORMAT_LABELS.get(fmt, fmt)
            value = all_results.get(label)
            if value is None:
                sent_messages.append(await m.reply_text(
                    f"⚠️ Couldn't generate {label} (missing library on the server)."
                ))
            else:
                sent_messages.append(await m.reply_text(f"🔹 <b>{label}</b>\n\n" + ui.session_result(value)))

        for sm in sent_messages:
            asyncio.create_task(_self_destruct(sm, delay=60))
    finally:
        # Wipe the client + any trace of phone/code/password/auth_key from
        # memory regardless of whether sending succeeded.
        await state.clear(user_id)


async def _self_destruct(message: Message, delay: int):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception:
        pass
