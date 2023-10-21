import datetime
from typing import List, TypeVar

T = TypeVar("T")


def split_list(input_list: List[T], n: int) -> List[List[T]]:
    if n <= 0:
        raise ValueError("Parameter n must be a positive integer")

    return [input_list[i : i + n] for i in range(0, len(input_list), n)]


def get_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))


def get_today() -> datetime.date:
    return get_now().date()


def shorten(text: str, max_length: int = 60) -> str:
    if len(text) > max_length:
        return text[: max_length - 3] + "..."
    return text
