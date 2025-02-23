import secrets
from typing import Any

from line import Cog, Context, command
from line.models import (
    ButtonsTemplate,
    ConfirmTemplate,
    ImageMessage,
    PostbackAction,
    TemplateMessage,
    URIAction,
)

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
                "此機器人使用 LINE Notify 來推播通知，如此才能在上市櫃公司發布重大訊息時即時通知您。因此，請先進行推播設定。",
                actions=[PostbackAction("進行推播設定", data="cmd=set_line_notify")],
            ),
        )

    @command
    async def continue_bot(self, ctx: Context) -> Any:
        await self.bot.link_rich_menu_to_users(self.bot.rich_menu_1_id, [ctx.user_id])
        await ctx.reply_text("✅ LINE Notify 設定成功，點擊「新增公司」即可開始追蹤上市櫃公司，並在它們發布重大訊息時即時收到通知")

    @command
    async def set_line_notify(self, ctx: Context) -> Any:
        user = await User.get(id=ctx.user_id)
        if not user.line_notify_token:
            state = secrets.token_urlsafe()
            user.line_notify_state = state
            await user.save()

            template = ButtonsTemplate(
                "目前尚未設定 LINE Notify\n\n請參考上方圖示步驟, 點擊下方「前往設定」按鈕後進行設定",
                [
                    URIAction(
                        label="前往設定",
                        uri=self.bot.line_notify_api.get_oauth_uri(state),
                    ),
                ],
                title="推播設定",
            )
            image = ImageMessage(
                original_content_url="https://i.imgur.com/C2DaGPf.png",
                preview_image_url="https://i.imgur.com/C2DaGPf.png",
            )
            await ctx.reply_multiple(
                [
                    image,
                    TemplateMessage("推播設定", template=template),
                ]
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
    async def send_test_message(self, ctx: Context) -> Any:
        user = await User.get(id=ctx.user_id)
        assert user.line_notify_token

        await self.bot.line_notify_api.notify(
            user.line_notify_token, message="這是一則測試訊息"
        )
        template = ButtonsTemplate(
            "已發送測試訊息",
            [
                URIAction(
                    label="點我前往查看", uri="https://line.me/R/oaMessage/%40linenotify"
                )
            ],
        )
        await ctx.reply_template("已發送測試訊息", template=template)

    @command
    async def reset_line_notify(self, ctx: Context) -> Any:
        template = ConfirmTemplate(
            "確定要解除綁定 LINE Notify 嗎?\n您將無法收到任何來自此機器人的推播訊息",
            [
                PostbackAction("確定", data="cmd=reset_line_notify_confirm"),
                PostbackAction("取消", data="cmd=reset_line_notify_cancel"),
            ],
        )
        await ctx.reply_template("確認取消設定", template=template)

    @command
    async def reset_line_notify_confirm(self, ctx: Context) -> Any:
        user = await User.get(id=ctx.user_id)
        await self.bot.session.post(
            "https://notify-api.line.me/api/revoke",
            headers={"Authorization": f"Bearer {user.line_notify_token}"},
        )

        user.line_notify_token = None
        user.line_notify_state = None
        await user.save()
        await self.bot.link_rich_menu_to_users(self.bot.rich_menu_3_id, [user.id])
        return await ctx.reply_text("✅ 已解除綁定 LINE Notify")

    @command
    async def reset_line_notify_cancel(self, ctx: Context) -> Any:
        await ctx.reply_text("已取消")
