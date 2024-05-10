from typing import Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from anipy_api.provider.base import LanguageTypeEnum


class BeautifulSoupLocationError(Exception):
    """Error that gets raised in the Provider if there are errors with parsing
    HTML content."""

    def __init__(self, what: str, where: str):
        """__init__ for BeautifulSoupLocationError.

        Args:
            what: What could not be parsed
            where: The url of the to be parsed content
        """
        super().__init__(f"Could not locate {what} at {where}")


class LangTypeNotAvailableError(Exception):
    """Error that gets raised in the Provider if the specified language type is
    not available."""

    def __init__(self, identifier: str, provider: str, lang: "LanguageTypeEnum"):
        """__init__ for LangTypeNotAvailableError.

        Args:
            identifier: Identifier of the Anime
            provider: Name of the Provider
            lang: The language that is not available
        """
        super().__init__(
            f"{str(lang).capitalize()} is not available for identifier `{identifier}` on provider `{provider}`"
        )


class MyAnimeListError(Exception):
    """Error that gets raised by [MyAnimeList][anipy_api.mal.MyAnimeList], this
    may include authentication errors or other HTTP errors."""

    def __init__(
        self, url: str, status: int, mal_api_error: Optional[Dict] = None
    ) -> None:
        """__init__ for MyAnimeListError.

        Args:
            url: Requested URL that caused the error
            status: HTTP status code
            mal_api_error: MyAnimeList api error if returned
        """
        error_text = f"Error requesting {url}, status is {status}."
        if mal_api_error:
            error_text = f"{error_text} Additional info from api {mal_api_error}"

        super().__init__(error_text)


class DownloadError(Exception):
    """Error that gets raised by
    [Downloader][anipy_api.download.Downloader]."""

    def __init__(self, message: str):
        """__init__ for DownloadError.

        Args:
            message: Failure reason
        """
        super().__init__(message)


class PlayerError(Exception):
    """Error that gets throws by certain functions in the player module."""

    def __init__(self, message: str):
        """__init__ for PlayerError.

        Args:
            message: Failure reason
        """
        super().__init__(message)


class ArgumentError(Exception):
    """Error that gets raised if something is wrong with the arguments provided to a callable."""

    def __init__(self, message: str):
        """__init__ for ArgumentError

        Args:
            message: Failure reason
        """
        super().__init__(message)
