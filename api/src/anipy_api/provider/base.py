from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Set, Union

from requests import Session

from anipy_api.provider.filter import FilterCapabilities, Filters, Status

Episode = Union[int, float]
"""Episode type, float or integer."""


class LanguageTypeEnum(Enum):
    """A enum that contains possible language types of anime.

    Attributes:
        SUB:
        DUB:
    """

    SUB = "sub"
    DUB = "dub"

    def __repr__(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value


@dataclass
class ProviderSearchResult:
    """A class that contains information about a search result.

    Attributes:
        identifier: The identifier of the anime
        name: The name of the anime
        languages: A set of supported language types for that anime
    """

    identifier: str
    name: str
    languages: Set[LanguageTypeEnum]

    def __hash__(self) -> int:
        return hash(self.identifier)


@dataclass
class ProviderInfoResult:
    """A class that contains detailed information about an anime.

    Attributes:
        name: Name of the Anime
        image: Image of the Anime
        genres: Genres of the Anime
        synopsis: Synopsis of the Anime
        release_year: Release year of the Anime
        status: Status of the anime
        alternative_names: List of alternative names
    """

    name: str
    image: Optional[str] = None
    genres: Optional[List[str]] = None
    synopsis: Optional[str] = None
    release_year: Optional[int] = None
    status: Optional[Status] = None
    alternative_names: Optional[List[str]] = None


@dataclass
class ProviderStream:
    """A class that contains information about a video stream.

    Attributes:
        url: The url of the stream.
        resolution: The resolution (actually the width)
            of the stream. (e.g. 1080, 720 etc.)
        episode: The episode this stream is from
        language: The language type this stream is in
    """

    url: str
    resolution: int
    episode: Episode
    language: LanguageTypeEnum

    def __hash__(self) -> int:
        return hash(self.url)


class BaseProvider(ABC):
    """
    This is the abstract base class for all the providers,
    use this as documentation to know how to use the providers.

    To get a list of Providers use the
    [list_providers][anipy_api.provider.provider.list_providers] function
    or use [get_provider][anipy_api.provider.provider.get_provider] to get a
    provider by name.

    Attributes:
        NAME: The name of the provider
        BASE_URL: The base url of the provider
        FILTER_CAPS: The filter capabilities of the provider
    """

    NAME: str
    BASE_URL: str
    FILTER_CAPS: FilterCapabilities

    def __init__(self, base_url_override: Optional[str] = None):
        """__init__ of BaseProvider

        Args:
            base_url_override: Override the url used by the provider.
        """
        if base_url_override is not None:
            self.BASE_URL = base_url_override

        self.session = Session()

    def __init_subclass__(cls) -> None:
        for v in ["NAME", "BASE_URL", "FILTER_CAPS"]:
            if not hasattr(cls, v):
                raise NotImplementedError(
                    "Attribute '{}' has not been overriden in class '{}'".format(
                        v, cls.__name__
                    )
                )

    @abstractmethod
    def get_search(
        self, query: str, filters: Filters = Filters()
    ) -> List[ProviderSearchResult]:
        """Search in the Provider.

        Args:
            query: The search query
            filters: The filter object, check FILTER_CAPS
                to see which filters this provider supports

        Returns:
            A list of search results
        """
        ...

    @abstractmethod
    def get_info(self, identifier: str) -> ProviderInfoResult:
        """Get detailed information about an anime.

        Args:
            identifier: The identifier of the anime

        Returns:
            A information object
        """
        ...

    @abstractmethod
    def get_episodes(self, identifier: str, lang: LanguageTypeEnum) -> List[Episode]:
        """Get a list of episodes of an anime.

        Args:
            identifier: The identifier of the anime
            lang: The language type used to look up the episode list

        Returns:
            A list of episodes

        Raises:
            LangTypeNotAvailableError: Raised when the language provided is
                not available for the anime
        """
        ...

    @abstractmethod
    def get_video(
        self, identifier: str, episode: Episode, lang: LanguageTypeEnum
    ) -> List[ProviderStream]:
        """Get a list of video streams for a anime episode.

        Args:
            identifier: The identifier of the anime
            episode: The episode to get the streams from
            lang: The language type used to look up the streams

        Returns:
            A list of video streams

        Raises:
            LangTypeNotAvailableError: Raised when the language provided is
                not available for the anime
        """
        ...

    def __str__(self) -> str:
        return self.NAME
