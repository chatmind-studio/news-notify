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
    title = fields.CharField(max_length=100)
    datetime = fields.DatetimeField()
    stock: fields.ForeignKeyRelation[Stock] = fields.ForeignKeyField(
        "models.Stock", related_name="news"
    )
    notified_users: fields.ManyToManyRelation[User] = fields.ManyToManyField(
        "models.User", related_name="notified_news"
    )

    class Meta:
        unique_together = ("title", "datetime", "stock")
        ordering = ["-datetime"]
