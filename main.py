import asyncio
from aiohttp import web

import config


async def _health(_request):
    return web.Response(text="ok")


async def run_web_server():
    app = web.Application()
    app.router.add_get("/", _health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", config.PORT)
    await site.start()


async def main():
    # Import handlers here (inside the running event loop) so Pyrogram's
    # internal asyncio.get_event_loop() call succeeds on Python 3.10+.
    from handlers import bot
    import ui

    await run_web_server()
    await bot.start()
    print(f"{ui.BOT_DISPLAY_NAME} is online.")
    await asyncio.Event().wait()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
