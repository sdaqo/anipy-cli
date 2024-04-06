from typing import Union, List, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass
from requests import Session

from anipy_cli.provider.filter import FilterCapabilities, Filters

Episode = Union[int, float]


@dataclass(frozen=True)
class ProviderSearchResult:
    identifier: str
    name: str
    dub: Optional[bool] = None

    def __hash__(self) -> int:
        return hash(self.identifier)


@dataclass(frozen=True)
class ProviderInfoResult:
    name: str
    image: Optional[str] = None
    genres: Optional[List[str]] = None
    synopsis: Optional[str] = None
    release_year: Optional[int] = None
    status: Optional[str] = None


@dataclass(frozen=True)
class ProviderStream:
    url: str
    resolution: int
    episode: Episode


class BaseProvider(ABC):
    NAME: str
    BASE_URL: str
    FILTER_CAPS: FilterCapabilities

    def __init__(self):
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
    def get_search(self, query: str, filters: Filters = Filters()) -> List[ProviderSearchResult]: ...

    @abstractmethod
    def get_episodes(self, identifier: str) -> List[Episode]: ...

    @abstractmethod
    def get_info(self, identifier: str) -> ProviderInfoResult: ...

    @abstractmethod
    def get_video(self, identifier: str, episode: Episode) -> List[ProviderStream]: ...
