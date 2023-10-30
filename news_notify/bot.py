import logging
import os
import sys
from pathlib import Path
from typing import Optional

from aiohttp import web
from line import Bot
from line.ext.notify import LineNotifyAPI
from linebot.v3.webhooks import FollowEvent, MessageEvent
from stock_crawl import StockCrawl
from tortoise import Tortoise
from tortoise.exceptions import IntegrityError

from .models import News, Stock, User
from .rich_menus import RICH_MENU_1, RICH_MENU_2, RICH_MENU_3
from .utils import get_now


class NewsNotify(Bot):
    def __init__(
        self, channel_secret: str, access_token: str, *, db_url: Optional[str] = None
    ):
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

    def _setup_line_notify(self):
        line_notify_client_id = os.getenv("LINE_NOTIFY_CLIENT_ID")
        if line_notify_client_id is None:
            raise RuntimeError("LINE_NOTIFY_CLIENT_ID is not set")
        line_notify_client_secret = os.getenv("LINE_NOTIFY_CLIENT_SECRET")
        if line_notify_client_secret is None:
            raise RuntimeError("LINE_NOTIFY_CLIENT_SECRET is not set")

        self.line_notify_api = LineNotifyAPI(
            client_id=line_notify_client_id,
            client_secret=line_notify_client_secret,
            redirect_uri=f"{self.app_url}/line-notify",
        )

    async def _line_notify_callback(self, request: web.Request) -> web.Response:
        params = await request.post()
        code = params.get("code")
        state = params.get("state")

        user = await User.get_or_none(line_notify_state=state)
        if user and isinstance(code, str):
            access_token = await self.line_notify_api.get_access_token(code)
            user.line_notify_token = access_token
            user.line_notify_state = None
            await user.save()
            await self.line_notify_api.notify(
                access_token,
                message=f"\n✅ LINE Notify 設定成功\n\n點擊此連結返回機器人:\nhttps://line.me/R/ti/p/%40{self.basic_id}",
            )
            await self.link_rich_menu_to_users(self.rich_menu_3_id, [user.id])

        return web.Response(
            status=302,
            headers={"Location": "https://line.me/R/oaMessage/%40linenotify"},
        )

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
        # run task every 15 minutes
        if now.minute % 15 == 0 and now.second < 1:
            await self.crawl_news()

    async def crawl_news(self) -> None:
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

            db_news, _ = await News.get_or_create(
                title=n.title,
                datetime=n.date_time,
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

                await self.line_notify_api.notify(
                    user.line_notify_token,
                    message=f"\n{db_stock}\n發言時間: {n.date_time.strftime('%Y/%m/%d %H:%M')}\n主旨: {n.title}\n\nGoogle 搜尋:\n{await db_news.google_search}",
                )
                await db_news.notified_users.add(user)

    async def setup_hook(self) -> None:
        logging.info("Setting up database")
        await Tortoise.init(
            db_url=self.db_url or "sqlite://db.sqlite3",
            modules={"models": ["news_notify.models"]},
        )
        await Tortoise.generate_schemas()

        logging.info("Setting up LINE Notify")
        self._setup_line_notify()
        self.app.add_routes([web.post("/line-notify", self._line_notify_callback)])

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
