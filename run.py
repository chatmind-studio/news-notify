import asyncio
import os

from dotenv import load_dotenv

from news_notify.bot import NewsNotify

load_dotenv()


async def main() -> None:
    channel_secret = os.getenv("LINE_CHANNEL_SECRET")
    access_token = os.getenv("LINE_ACCESS_TOKEN")
    if not (channel_secret and access_token):
        msg = "LINE_CHANNEL_SECRET and LINE_ACCESS_TOKEN are required."
        raise RuntimeError(msg)

    bot = NewsNotify(channel_secret, access_token, db_url=os.getenv("DB_URL"))
    await bot.run(port=8001)


asyncio.run(main())
