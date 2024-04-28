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


def memoized_method(*lru_args, **lru_kwargs):
    """Decorator to memoize a class method (see: [https://stackoverflow.com/a/33672499](https://stackoverflow.com/a/33672499))

    Args:
        *lru_args: Args to pass to `functools.lru_cache`.
        **lru_kwargs: Kwargs to pass to `functools.lru_cache`
    """
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
