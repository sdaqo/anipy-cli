from abc import ABC, abstractmethod
from dataclasses import dataclass, fields
from enum import Enum, Flag, auto
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from requests import Request


class Season(Enum):
    """

    Attributes: 
        SPRING: 
        SUMMER: 
        FALL: 
        WINTER: 
    """
    SPRING = auto()
    SUMMER = auto()
    FALL = auto()
    WINTER = auto()


class Status(Enum):
    """

    Attributes: 
        UPCOMING: 
        ONGOING: 
        COMPLETED: 
    """
    UPCOMING = auto()
    ONGOING = auto()
    COMPLETED = auto()


class MediaType(Enum):
    """

    Attributes: 
        TV: 
        MOVIE: 
        OVA: 
        ONA: 
        SPECIAL: 
        MUSIC: 
    """
    TV = auto()
    MOVIE = auto()
    OVA = auto()
    ONA = auto()
    SPECIAL = auto()
    MUSIC = auto()


@dataclass
class Filters:
    """

    Attributes: 
        year: 
        season: 
        status: 
        media_type: 
    """
    year: Optional[List[int]] = None
    season: Optional[List[Season]] = None
    status: Optional[List[Status]] = None
    media_type: Optional[List[MediaType]] = None


class FilterCapabilities(Flag):
    """

    Attributes: 
        YEAR: 
        SEASON: 
        STATUS: 
        MEDIA_TYPE: 
        ALL: 
    """
    YEAR = auto()
    SEASON = auto()
    STATUS = auto()
    MEDIA_TYPE = auto()
    ALL = YEAR | SEASON | STATUS | MEDIA_TYPE


class BaseFilter(ABC):
    """"""
    def __init__(self, request: "Request"):
        self._request = request

    @abstractmethod
    def _apply_query(self, query: str): ...

    @abstractmethod
    def _apply_year(self, year: List[int]): ...

    @abstractmethod
    def _apply_season(self, season: List[Season]): ...

    @abstractmethod
    def _apply_status(self, status: List[Status]): ...

    @abstractmethod
    def _apply_media_type(self, media_type: List[MediaType]): ...

    @staticmethod
    def _map_enum_members(values, map):
        mapped = []
        for m in values:
            mapped.append(map[m])
        return mapped

    def apply(self, query: str, filters: Filters) -> "Request":
        self._apply_query(query)

        for filter in fields(filters):
            value = getattr(filters, filter.name)
            if not value:
                continue

            func = self.__getattribute__(f"_apply_{filter.name}")
            func(value)

        return self._request
