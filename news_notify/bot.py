import logging
import sys
from pathlib import Path

from line import Bot
from linebot.v3.webhooks import FollowEvent, MessageEvent
from stock_crawl import StockCrawl
from tortoise import Tortoise
from tortoise.exceptions import IntegrityError

from .models import News, Stock, User
from .rich_menus import RICH_MENU_1, RICH_MENU_2, RICH_MENU_3
from .utils import get_now, send_webhook


class NewsNotify(Bot):
    def __init__(
        self, channel_secret: str, access_token: str, *, db_url: str | None = None
    ) -> None:
        super().__init__(channel_secret=channel_secret, access_token=access_token)
        self.db_url = db_url
        self.crawl = StockCrawl()
        self.basic_id = "847mdfxp"
        self.app_url = (
            "https://news-notify-linebot.seriaati.xyz"
            if sys.platform == "linux"
            else "https://vastly-assuring-grub.ngrok-free.app"
        )
        self.task_interval = 1

    async def on_follow(self, event: FollowEvent) -> None:
        try:
            await User.create(id=event.source.user_id)  # type: ignore
        except IntegrityError:
            pass

    async def on_message(self, event: MessageEvent) -> None:
        if event.message is None:
            return
        text: str = event.message.text  # type: ignore
        user = await User.get(id=event.source.user_id)  # type: ignore
        if user.temp_data:
            event.message.text = user.temp_data.format(text=text)  # type: ignore
            user.temp_data = None
            await user.save()

        await super().on_message(event)

    async def run_tasks(self) -> None:
        now = get_now()
        # run task every 30 minutes
        if now.minute % 30 == 0 and now.second < 1:
            await self.crawl_news()

    async def crawl_news(self) -> None:
        now = get_now()
        # do not crawl news between 11pm and 6am
        if 23 <= now.hour <= 6:
            return

        news = await self.crawl.fetch_news()
        for n in news:
            db_stock = await Stock.get_or_none(id=n.stock_id)
            if db_stock is None:
                fetched_stock = await self.crawl.fetch_stock(n.stock_id)
                if fetched_stock is None:
                    continue
                db_stock = await Stock.create(
                    id=fetched_stock.id, name=fetched_stock.name
                )

            news_id = f"{n.stock_id}_{n.date_of_speech}_{n.time_of_speech}"[:100]
            db_news = await News.get_or_none(id=news_id)
            if db_news is None:
                db_news = await News.create(
                    id=news_id,
                    data=n.model_dump_json(),
                    stock=db_stock,
                )

            await db_news.fetch_related("notified_users")
            notified_users = await db_news.notified_users.all()
            users = await User.filter(stocks__id=n.stock_id)
            for user in users:
                if user in notified_users:
                    continue
                if user.line_notify_token is None:
                    continue

                await send_webhook(
                    f"{db_stock}\n{db_news}\nhttps://goodinfo.tw/tw/StockDetail.asp?STOCK_ID={n.stock_id}",
                    url=user.line_notify_token,
                )
                await db_news.notified_users.add(user)

    async def setup_hook(self) -> None:
        logging.info("Setting up database")
        await Tortoise.init(
            db_url=self.db_url or "sqlite://db.sqlite3",
            modules={"models": ["news_notify.models"]},
        )
        await Tortoise.generate_schemas()

        logging.info("Loading cogs")
        for cog in Path("news_notify/cogs").glob("*.py"):
            logging.info("Loading cog %s", cog.stem)
            self.add_cog(f"news_notify.cogs.{cog.stem}")

        logging.info("Setting up rich menus")
        await self.delete_all_rich_menus()
        self.rich_menu_1_id = await self.create_rich_menu(
            RICH_MENU_1, "assets/rich_menu_1.png"
        )
        self.rich_menu_2_id = await self.create_rich_menu(
            RICH_MENU_2, "assets/rich_menu_2.png"
        )
        await self.line_bot_api.set_default_rich_menu(self.rich_menu_2_id)
        self.rich_menu_3_id = await self.create_rich_menu(
            RICH_MENU_3, "assets/rich_menu_3.png"
        )
        users = await User.all()
        linked = [user.id for user in users if user.line_notify_token]
        if linked:
            await self.link_rich_menu_to_users(self.rich_menu_1_id, linked)

    async def on_close(self) -> None:
        await Tortoise.close_connections()
        await self.crawl.close()
