from typing import Optional

from tortoise import fields
from tortoise.models import Model


class User(Model):
    id = fields.CharField(max_length=33, pk=True)
    stocks: fields.ManyToManyRelation["Stock"] = fields.ManyToManyField(
        "models.Stock", related_name="users"
    )
    line_notify_token: Optional[str] = fields.CharField(max_length=255, null=True)  # type: ignore
    line_notify_state: Optional[str] = fields.CharField(max_length=255, null=True)  # type: ignore
    temp_data: Optional[str] = fields.TextField(null=True)  # type: ignore
    notified_news: fields.ManyToManyRelation["News"]


class Stock(Model):
    id = fields.CharField(max_length=10, pk=True)
    name = fields.CharField(max_length=20)
    news: fields.ReverseRelation["News"]
    users: fields.ManyToManyRelation[User]

    def __str__(self) -> str:
        return f"[{self.id}] {self.name}"


class News(Model):
    id = fields.CharField(max_length=100, pk=True)
    data: fields.Field[dict[str, str]] = fields.JSONField()  # type: ignore
    stock: fields.ForeignKeyRelation[Stock] = fields.ForeignKeyField(
        "models.Stock", related_name="news"
    )
    notified_users: fields.ManyToManyRelation[User] = fields.ManyToManyField(
        "models.User", related_name="notified_news"
    )

    def __str__(self) -> str:
        return (
            f"發言日期: {self.data['date_of_speech']}\n"
            f"事實發生日: {self.data['date_of_occurrence']}\n"
            f"符合條款: {self.data['terms_complied']}\n"
            f"主旨: {self.data['title']}\n\n"
            f"說明:\n{self.data['explanation']}\n"
        )
