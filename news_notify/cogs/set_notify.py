from typing import Any

from line import Cog, Context, command
from line.models import (
    ButtonsTemplate,
    ConfirmTemplate,
    PostbackAction,
)

from news_notify.utils import send_webhook

from ..bot import NewsNotify
from ..models import User


class SetNotifyCog(Cog):
    def __init__(self, bot: NewsNotify) -> None:
        super().__init__(bot)
        self.bot = bot

    @command
    async def start(self, ctx: Context) -> Any:
        await ctx.reply_template(
            "開始使用",
            template=ButtonsTemplate(
                "此機器人使用 Discord Webhook 來推播通知，如此才能在上市櫃公司發布重大訊息時即時通知您。因此，請先進行推播設定。",
                actions=[PostbackAction("進行推播設定", data="cmd=set_line_notify")],
            ),
        )

    @command
    async def continue_bot(self, ctx: Context) -> Any:
        await self.bot.link_rich_menu_to_users(self.bot.rich_menu_1_id, [ctx.user_id])
        await ctx.reply_text(
            "✅ Discord Webhook 設定成功，點擊「新增公司」即可開始追蹤上市櫃公司，並在它們發布重大訊息時即時收到通知"
        )

    @command
    async def set_line_notify(self, ctx: Context) -> Any:
        user = await User.get(id=ctx.user_id)
        if not user.line_notify_token:
            user.temp_data = "cmd=set_webhook_url&url={text}"
            await user.save()
            await ctx.reply_template(
                "設置 Discord Webhook",
                template=ButtonsTemplate(
                    "請輸入您的 Discord Webhook 連結, 以便接收推播訊息",
                    actions=[
                        PostbackAction(
                            "輸入連結", data="none", input_option="openKeyboard"
                        ),
                    ],
                ),
            )
        else:
            template = ButtonsTemplate(
                "✅ 已完成設定",
                [
                    PostbackAction("發送測試訊息", data="cmd=send_test_message"),
                    PostbackAction("解除綁定", data="cmd=reset_line_notify"),
                ],
                title="推播設定",
            )
            await ctx.reply_template("推播設定", template=template)

    @command
    async def set_webhook_url(self, ctx: Context, url: str) -> Any:
        user = await User.get(id=ctx.user_id)
        user.line_notify_token = url
        await user.save()
        await self.bot.link_rich_menu_to_users(self.bot.rich_menu_3_id, [user.id])
        return await ctx.reply_text("✅ Discord Webhook 設定成功")

    @command
    async def send_test_message(self, ctx: Context) -> Any:
        user = await User.get(id=ctx.user_id)
        assert user.line_notify_token

        await send_webhook("這是一則測試訊息", url=user.line_notify_token)
        await ctx.reply_text("✅ 已發送測試訊息")

    @command
    async def reset_line_notify(self, ctx: Context) -> Any:
        template = ConfirmTemplate(
            "確定要解除綁定 Discord Webhook 嗎?\n您將無法收到任何來自此機器人的推播訊息",
            [
                PostbackAction("確定", data="cmd=reset_line_notify_confirm"),
                PostbackAction("取消", data="cmd=reset_line_notify_cancel"),
            ],
        )
        await ctx.reply_template("確認取消設定", template=template)

    @command
    async def reset_line_notify_confirm(self, ctx: Context) -> Any:
        user = await User.get(id=ctx.user_id)
        user.line_notify_token = None
        user.line_notify_state = None
        await user.save()
        await self.bot.link_rich_menu_to_users(self.bot.rich_menu_2_id, [user.id])
        return await ctx.reply_text("✅ 已解除綁定 Discord Webhook")

    @command
    async def reset_line_notify_cancel(self, ctx: Context) -> Any:
        await ctx.reply_text("已取消")
