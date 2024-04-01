from abc import ABC, abstractmethod
from typing import Union, List, Optional
from dataclasses import dataclass
from requests import Session

Episode = Union[int, float]


@dataclass
class ProviderSearchResult:
    identifier: str
    name: str
    dub: Optional[bool]


@dataclass
class ProviderInfoResult:
    name: str
    image: Optional[str]
    genres: Optional[List[str]]
    synopsis: Optional[str]
    release_year: Optional[int]
    status: Optional[str]


@dataclass
class ProviderStream:
    url: str
    resolution: int
    episode: Episode


class BaseProvider(ABC):
    NAME: str
    BASE_URL: str

    def __init__(self):
        self.session = Session()

    def __init_subclass__(cls) -> None:
        for v in ["NAME", "BASE_URL"]:
            if not hasattr(cls, v):
                raise NotImplementedError(
                    "Attribute '{}' has not been overriden in class '{}'".format(
                        v, cls.__name__
                    )
                )

    @abstractmethod
    def get_search(self, query: str) -> List[ProviderSearchResult]: ...

    @abstractmethod
    def get_episodes(self, identifier: str) -> List[Episode]: ...

    @abstractmethod
    def get_info(self, identifier: str) -> ProviderInfoResult: ...

    @abstractmethod
    def get_video(self, identifier: str, episode: Episode) -> List[ProviderStream]: ...
