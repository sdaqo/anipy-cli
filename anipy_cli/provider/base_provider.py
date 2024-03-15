from abc import ABC, abstractmethod
from typing import Union, List, Optional, NewType, TypeVar
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
    def __init__(self):
        self.session = Session()

    @staticmethod 
    @abstractmethod
    def name() -> str:
        ...

    @abstractmethod
    def get_search(self, query: str) -> List[ProviderSearchResult]:
        ...
        
    @abstractmethod
    def get_episodes(self, identifier: str) -> List[Episode]:
        ...

    @abstractmethod
    def get_info(self, identifier: str) -> ProviderInfoResult:
        ...

    @abstractmethod
    def get_video(self, identifier: str, episode: Episode) -> List[ProviderStream]:
        ...

ProviderBaseType = TypeVar("ProviderBaseType", bound=BaseProvider)
