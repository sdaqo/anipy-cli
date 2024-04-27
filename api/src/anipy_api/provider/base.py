from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Set, Union

from requests import Session

from anipy_api.provider.filter import FilterCapabilities, Filters

Episode = Union[int, float]


class LanguageTypeEnum(Enum):
    """

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
    """

    Attributes:
        identifier:
        name:
        languages:
    """

    identifier: str
    name: str
    languages: Set[LanguageTypeEnum]

    def __hash__(self) -> int:
        return hash(self.identifier)


@dataclass
class ProviderInfoResult:
    """

    Attributes:
        name:
        image:
        genres:
        synopsis:
        release_year:
        status:
        alternative_names:
    """

    name: str
    image: Optional[str] = None
    genres: Optional[List[str]] = None
    synopsis: Optional[str] = None
    release_year: Optional[int] = None
    status: Optional[str] = None
    alternative_names: Optional[List[str]] = None


@dataclass
class ProviderStream:
    """

    Attributes:
        url:
        resolution:
        episode:
        language:
    """

    url: str
    resolution: int
    episode: Episode
    language: LanguageTypeEnum

    def __hash__(self) -> int:
        return hash(self.url)


class BaseProvider(ABC):
    """
    Args:
        base_url_override: Override the url used by the provider.

    Attributes:
        NAME:
        BASE_URL:
        FILTER_CAPS:
    """

    NAME: str
    BASE_URL: str
    FILTER_CAPS: FilterCapabilities

    def __init__(self, base_url_override: Optional[str] = None):
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
        """

        Args:
            query: 
            filters: 

        Returns:
            
        """
        ...

    @abstractmethod
    def get_info(self, identifier: str) -> ProviderInfoResult: 
        """

        Args:
            identifier: 

        Returns:
            
        """
        ...

    @abstractmethod
    def get_episodes(
        self, identifier: str, lang: LanguageTypeEnum
    ) -> List[Episode]: 
        """

        Args:
            identifier: 
            lang: 

        Returns:
            dasda
            
        """
        ...

    @abstractmethod
    def get_video(
        self, identifier: str, episode: Episode, lang: LanguageTypeEnum
    ) -> List[ProviderStream]: 
        """

        Args:
            identifier: 
            episode: 
            lang: 

        Returns:
            
        """
        ...
