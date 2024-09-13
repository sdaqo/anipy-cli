"""These are only internal utils, which are not made to be used outside"""

from typing import TYPE_CHECKING
from typing import Union, Optional

if TYPE_CHECKING:
    from requests import Request, Session, Response
    from bs4 import Tag, NavigableString


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


def safe_attr(
    bs_obj: Optional[Union["Tag", "NavigableString", int]], attr: str
) -> Optional[str]:
    if bs_obj is None or isinstance(bs_obj, int):
        return None

    if attr == "text":
        return bs_obj.get_text()

    return bs_obj.get(attr)  # type: ignore
