from typing import Any

from line import Cog, Context, command
from line.models import (
    CarouselColumn,
    CarouselTemplate,
    PostbackAction,
    QuickReply,
    QuickReplyItem,
)

from ..bot import NewsNotify
from ..models import News, Stock, User
from ..utils import shorten, split_list


class StockCog(Cog):
    def __init__(self, bot: NewsNotify) -> None:
        super().__init__(bot)
        self.bot = bot

    @command
    async def add_company(
        self, ctx: Context, stock_id_or_name: str | None = None
    ) -> Any:
        user = await User.get(id=ctx.user_id).prefetch_related("stocks")

        if stock_id_or_name is None:
            user.temp_data = "cmd=add_company&stock_id_or_name={text}"
            await user.save()
            await ctx.reply_text(
                "請輸入欲新增的公司的股票代號或公司簡稱\n例如: 「2330」或「台積電」",
                quick_reply=QuickReply(
                    [
                        QuickReplyItem(
                            action=PostbackAction(label="✖️ 取消", data="cmd=cancel")
                        )
                    ]
                ),
            )
        else:
            stock = await self.bot.crawl.fetch_stock(stock_id_or_name)
            if stock is None:
                return await ctx.reply_text(
                    f"❌ 錯誤\n找不到簡稱或代號為「{stock_id_or_name}」的股票",
                    quick_reply=QuickReply(
                        [
                            QuickReplyItem(
                                action=PostbackAction(
                                    label="🔄️ 重新輸入",
                                    data="cmd=add_company",
                                    input_option="openKeyboard",
                                )
                            ),
                            QuickReplyItem(
                                action=PostbackAction(label="✖️ 取消", data="cmd=cancel")
                            ),
                        ]
                    ),
                )
            db_stock, _ = await Stock.get_or_create(id=stock.id, name=stock.name)
            await db_stock.users.add(user)
            await ctx.reply_text(
                f"✅ 成功\n已新增 {db_stock}, 您將會開始收到來自 {db_stock} 的重大訊息通知",
                quick_reply=QuickReply(
                    [
                        QuickReplyItem(
                            action=PostbackAction(
                                label="➕ 繼續新增",
                                data="cmd=add_company",
                                input_option="openKeyboard",
                            )
                        ),
                        QuickReplyItem(
                            action=PostbackAction(label="✖️ 先這樣", data="cmd=cancel")
                        ),
                    ]
                ),
            )
        return None

    @command
    async def cancel(self, ctx: Context) -> Any:
        await ctx.reply_text(
            "已取消",
            quick_reply=QuickReply(
                [
                    QuickReplyItem(
                        PostbackAction(label="💼 管理公司", data="cmd=view_companies")
                    )
                ]
            ),
        )

    @command
    async def search_company(self, ctx: Context) -> Any:
        user = await User.get(id=ctx.user_id)
        user.temp_data = "cmd=view_companies&stock_id_or_name={text}"
        await user.save()
        await ctx.reply_text(
            "請輸入欲查詢的公司的股票代號或簡稱\n例如:「2330」或「台積電」",
            quick_reply=QuickReply(
                [QuickReplyItem(PostbackAction(label="✖️ 取消", data="cmd=cancel"))]
            ),
        )

    @command
    async def view_companies(
        self, ctx: Context, index: int = 0, stock_id_or_name: str | None = None
    ) -> Any:
        user = await User.get(id=ctx.user_id).prefetch_related("stocks")
        stocks = await user.stocks.all().prefetch_related("news")

        if stock_id_or_name:
            stocks = [
                stock
                for stock in stocks
                if stock_id_or_name in stock.id or stock_id_or_name in stock.name
            ]

        if not stocks:
            return await ctx.reply_text(
                "目前還沒有新增任何公司",
                quick_reply=QuickReply(
                    [
                        QuickReplyItem(
                            PostbackAction(
                                label="➕ 新增公司",
                                data="cmd=add_company",
                                input_option="openKeyboard",
                            )
                        )
                    ]
                ),
            )

        split_stocks = split_list(stocks, 10)
        columns: list[CarouselColumn] = []
        for stock in split_stocks[index]:
            news_count = await stock.news.all().count()
            column = CarouselColumn(
                title=str(stock),
                text=f"目前已推播過 {news_count} 則重大訊息",
                actions=[
                    PostbackAction(
                        "📢 查看歷史重大訊息", data=f"cmd=view_news&stock_id={stock.id}"
                    ),
                    PostbackAction(
                        "✖️ 取消追蹤", data=f"cmd=delete_company&stock_id={stock.id}"
                    ),
                ],
            )
            columns.append(column)

        quick_reply_items: list[QuickReplyItem] = []
        if index > 0:
            quick_reply_items.append(
                QuickReplyItem(
                    action=PostbackAction(
                        label="⬅️ 上一頁", data=f"cmd=view_companies&index={index - 1}"
                    )
                ),
            )
        if index < len(split_stocks) - 1:
            quick_reply_items.append(
                QuickReplyItem(
                    action=PostbackAction(
                        label="➡️ 下一頁", data=f"cmd=view_companies&index={index + 1}"
                    )
                )
            )

        quick_reply_items.append(
            QuickReplyItem(
                action=PostbackAction(
                    label="🔎 搜尋公司",
                    data="cmd=search_company",
                    input_option="openKeyboard",
                )
            )
        )

        await ctx.reply_template(
            "管理公司",
            template=CarouselTemplate(columns=columns),
            quick_reply=QuickReply(items=quick_reply_items)
            if quick_reply_items
            else None,
        )
        return None

    @command
    async def delete_company(self, ctx: Context, stock_id: str) -> Any:
        user = await User.get(id=ctx.user_id)
        stock = await Stock.get(id=stock_id)
        await user.stocks.remove(stock)
        await ctx.reply_text(
            f"✖️ 已取消追蹤 {stock}, 您將不會再收到來自 {stock} 的重大訊息通知",
            quick_reply=QuickReply(
                [
                    QuickReplyItem(
                        PostbackAction(
                            label="➕ 新增公司",
                            data="cmd=add_company",
                            input_option="openKeyboard",
                        )
                    ),
                    QuickReplyItem(
                        PostbackAction(label="💼 管理公司", data="cmd=view_companies")
                    ),
                ]
            ),
        )

    @command
    async def view_news(self, ctx: Context, stock_id: str, index: int = 0) -> Any:
        stock = await Stock.get(id=stock_id).prefetch_related("news")
        news = await stock.news.all()
        if not news:
            return await ctx.reply_text(
                "目前還沒有推播過任何此公司的重大訊息",
                quick_reply=QuickReply(
                    [
                        QuickReplyItem(
                            PostbackAction(label="↩️ 返回", data="cmd=view_companies")
                        )
                    ]
                ),
            )

        split_news = split_list(news, 10)
        columns: list[CarouselColumn] = []
        for news in split_news[index]:
            column = CarouselColumn(
                text=shorten(news.data["title"]),
                actions=[
                    PostbackAction(
                        "查看詳情", data=f"cmd=show_news_detail&news_id={news.id}&stock_id={stock_id}"
                    ),
                ],
            )
            columns.append(column)

        quick_reply_items: list[QuickReplyItem] = []
        if index > 0:
            quick_reply_items.append(
                QuickReplyItem(
                    action=PostbackAction(
                        label="⬅️ 上一頁",
                        data=f"cmd=view_news&stock_id={stock_id}&index={index - 1}",
                    )
                ),
            )
        if index < len(split_news) - 1:
            quick_reply_items.append(
                QuickReplyItem(
                    action=PostbackAction(
                        label="➡️ 下一頁",
                        data=f"cmd=view_news&stock_id={stock_id}&index={index + 1}",
                    )
                )
            )

        await ctx.reply_template(
            f"{stock} 發布過的重大訊息",
            template=CarouselTemplate(columns=columns),
            quick_reply=QuickReply(items=quick_reply_items)
            if quick_reply_items
            else None,
        )
        return None

    @command
    async def show_news_detail(self, ctx: Context, news_id: str, stock_id: str) -> None:
        news = await News.get(id=news_id)
        text = f"{news}\n\nhttps://goodinfo.tw/tw/StockDetail.asp?STOCK_ID={stock_id}"
        await ctx.reply_text(text)
