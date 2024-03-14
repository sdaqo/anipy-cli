from abc import ABC, abstractmethod
from typing import Union, List, Optional
from dataclasses import dataclass
from requests import Session

@dataclass
class ProviderSearchResult:
    identifier: str
    name: str
    dub: Optional[bool]


@dataclass 
class ProviderInfoResult:
    image: Optional[str]
    genres: Optional[List[str]]
    synopsis: Optional[str]
    release_year: Optional[int]
    status: Optional[str]

@dataclass
class ProviderStream:
    stream: str
    resolution: int


class BaseProvider(ABC):
    session: Session

    @abstractmethod
    def get_search(self, query: str) -> List[ProviderSearchResult]:
        pass
        
    @abstractmethod
    def get_episodes(self, identifier: str) -> List[Union[int, float]]:
        pass

    @abstractmethod
    def get_info(self, identifier: str) -> ProviderInfoResult:
        pass

    @abstractmethod
    def get_video(self, identifier: str, episode: Union[int, float]) -> List[ProviderStream]:
        pass
