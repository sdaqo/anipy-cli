"""These are only internal utils, which are not made to be used outside"""

import functools
import weakref
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from requests import Request, Session, Response


def request_page(session: "Session", req: "Request") -> "Response":
    """Prepare a request and send it.

    Args:
        session: The requests session
        req: The request

    Returns:
        Response of the request
    """
    prepped = req.prepare()
    prepped.headers["User-Agent"] = (
        "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"
    )
    res = session.send(prepped)
    res.raise_for_status()
    return res


def parsenum(n: str):
    """Parse a number be it a integer or float

    Args:
        n: Number as a string

    Returns:

    """
    try:
        return int(n)
    except ValueError:
        return float(n)


def weak_lru(maxsize: int = 128):
    """Decorator to memoize a class method
    (see: [https://stackoverflow.com/a/68052994](https://stackoverflow.com/a/68052994))

    Args:
        maxsize: Maximum cache size
    """

    def wrapper(func):
        @functools.lru_cache(maxsize)
        def _func(_self, *args, **kwargs):
            return func(_self(), *args, **kwargs)

        @functools.wraps(func)
        def inner(self, *args, **kwargs):
            return _func(weakref.ref(self), *args, **kwargs)

        return inner

    return wrapper
