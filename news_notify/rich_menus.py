from line.models import PostbackAction, URIAction
from linebot.v3.messaging import (
    RichMenuArea,
    RichMenuBounds,
    RichMenuRequest,
    RichMenuSize,
)

RICH_MENU_1 = RichMenuRequest(
    size=RichMenuSize(width=1200, height=400),
    selected=True,
    name="rich_menu_1",
    chatBarText="打開/關閉導覽列",
    areas=[
        RichMenuArea(
            bounds=RichMenuBounds(x=26, y=18, width=190, height=170),
            action=PostbackAction(data="cmd=set_line_notify", label="推播設定"),
        ),
        RichMenuArea(
            bounds=RichMenuBounds(x=238, y=18, width=457, height=170),
            action=PostbackAction(
                data="cmd=add_company", label="新增公司", input_option="openKeyboard"
            ),
        ),
        RichMenuArea(
            bounds=RichMenuBounds(x=717, y=18, width=457, height=170),
            action=PostbackAction(data="cmd=view_companies", label="管理公司"),
        ),
        RichMenuArea(
            bounds=RichMenuBounds(x=26, y=212, width=190, height=170),
            action=PostbackAction(data="cmd=donate", label="支持贊助"),
        ),
        RichMenuArea(
            bounds=RichMenuBounds(x=238, y=212, width=457, height=170),
            action=URIAction(
                uri="https://line.me/R/nv/recommendOA/%40847mdfxp", label="推薦好友"
            ),
        ),
        RichMenuArea(
            bounds=RichMenuBounds(x=717, y=212, width=457, height=170),
            action=PostbackAction(data="cmd=about", label="關於我們"),
        ),
    ],
)

RICH_MENU_2 = RichMenuRequest(
    size=RichMenuSize(width=1200, height=600),
    selected=True,
    name="rich_menu_2",
    chatBarText="開始使用",
    areas=[
        RichMenuArea(
            bounds=RichMenuBounds(x=0, y=0, width=1200, height=600),
            action=PostbackAction(data="cmd=start", label="開始使用"),
        ),
    ],
)

RICH_MENU_3 = RichMenuRequest(
    size=RichMenuSize(width=1200, height=600),
    selected=True,
    name="rich_menu_3",
    chatBarText="✅ 設定完成",
    areas=[
        RichMenuArea(
            bounds=RichMenuBounds(x=0, y=0, width=1200, height=600),
            action=PostbackAction(data="cmd=continue_bot", label="設定完成 點我繼續"),
        ),
    ],
)
