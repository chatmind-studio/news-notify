import datetime
from typing import TypeVar

import aiohttp

T = TypeVar("T")


def split_list[T](input_list: list[T], n: int) -> list[list[T]]:
    if n <= 0:
        msg = "Parameter n must be a positive integer"
        raise ValueError(msg)

    return [input_list[i : i + n] for i in range(0, len(input_list), n)]


def get_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))


def get_today() -> datetime.date:
    return get_now().date()


def shorten(text: str, max_length: int = 60) -> str:
    if len(text) > max_length:
        return text[: max_length - 3] + "..."
    return text


async def send_webhook(message: str, *, url: str) -> None:
    async with aiohttp.ClientSession() as session:
        await session.post(url, json={"content": message})
