from requests import Request, Session, Response
from anipy_cli.provider.error import RequestError

def request_page(session: Session, req: Request) -> Response:
    prepped = req.prepare()
    prepped.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"
    res = session.send(prepped)
    if res.ok:
        return res
    else:
        raise RequestError(res.url, res.status_code)



