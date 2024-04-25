from typing import Dict, Optional


class BeautifulSoupLocationError(Exception):
    def __init__(self, what: str, where: str):
        super().__init__(f"Could not locate {what} at {where}")


class DubNotAvailableError(Exception):
    def __init__(self, identifier: str, provider: str):
        super().__init__(
            f"Dub is not available for identifier `{identifier}` on provider `{provider}`"
        )


class MyAnimeListError(Exception):
    def __init__(
        self, url: str, status: int, mal_api_error: Optional[Dict] = None
    ) -> None:
        error_text = f"Error requesting {url}, status is {status}."
        if mal_api_error:
            error_text = f"{error_text} Additional info from api {mal_api_error}"

        super().__init__(error_text)


class DownloadError(Exception):
    def __init__(self, message):
        super().__init__(message)


class PlayerError(Exception):
    def __init__(self, message):
        super().__init__(message)
