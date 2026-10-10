import asyncio
from aiohttp import web

import config
from handlers import bot


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
    await run_web_server()
    await bot.start()
    print(f"{__import__('ui').BOT_DISPLAY_NAME} is online.")
    await asyncio.Event().wait()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
