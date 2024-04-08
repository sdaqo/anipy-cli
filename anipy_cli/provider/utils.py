import functools
import weakref
from typing import TYPE_CHECKING

from anipy_cli.error import RequestError
from anipy_cli.provider.providers import *

if TYPE_CHECKING:
    from requests import Request, Session, Response


def request_page(session: "Session", req: "Request") -> "Response":
    prepped = req.prepare()
    prepped.headers["User-Agent"] = (
        "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"
    )
    res = session.send(prepped)
    res.raise_for_status()
    return res


def parsenum(n: str):
    try:
        return int(n)
    except ValueError:
        return float(n)


def memoized_method(*lru_args, **lru_kwargs):
    def decorator(func):
        @functools.wraps(func)
        def wrapped_func(self, *args, **kwargs):
            self_weak = weakref.ref(self)

            @functools.wraps(func)
            @functools.lru_cache(*lru_args, **lru_kwargs)
            def cached_method(*args, **kwargs):
                return func(self_weak(), *args, **kwargs)

            setattr(self, func.__name__, cached_method)
            return cached_method(*args, **kwargs)

        return wrapped_func

    return decorator
