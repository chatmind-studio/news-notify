from line import Cog, Context, command
from line.models import PostbackAction, QuickReply, QuickReplyItem

from ..bot import NewsNotify

OWNER_ID = "Udfc687303c03a91398d74cbfd33dcea4"


class AdminCog(Cog):
    def __init__(self, bot: NewsNotify):
        super().__init__(bot)
        self.bot = bot

    @command
    async def admin(self, ctx: Context):
        if ctx.user_id != OWNER_ID:
            return
        items = [
            QuickReplyItem(
                action=PostbackAction(
                    label="crawl news",
                    data="cmd=crawl_news",
                ),
            ),
        ]
        await ctx.reply_text("管理員界面", quick_reply=QuickReply(items=items))

    @command
    async def crawl_news(self, ctx: Context):
        if ctx.user_id != OWNER_ID:
            return
        await ctx.reply_text("crawling news...")
        await self.bot.crawl_news()

    @command
    async def get_user_id(self, ctx: Context) -> None:
        await ctx.reply_text(ctx.user_id)
