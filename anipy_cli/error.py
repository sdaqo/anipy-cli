class BeautifulSoupLocationError(Exception):
    def __init__(self, what: str, where: str):
        super().__init__(f"Could not locate {what} at {where}")


class RequestError(Exception):
    def __init__(self, url: str, status: int):
        super().__init__(f"Could not request `{url}`, status is {status}")


class DownloadError(Exception):
    def __init__(self, message):
        super().__init__(message)


class PlayerError(Exception):
    def __init__(self, message):
        super().__init__(message)
