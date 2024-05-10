from abc import ABC, abstractmethod
from dataclasses import dataclass, fields
from enum import Enum, Flag, auto
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from requests import Request


class Season(Enum):
    """A enum of seasons to filter by

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
    """A enum of anime states to filter by

    Attributes:
        UPCOMING:
        ONGOING:
        COMPLETED:
    """

    UPCOMING = auto()
    ONGOING = auto()
    COMPLETED = auto()


class MediaType(Enum):
    """A enum of mediatypes to filter by

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
    """A flter class that acts as a filter collection

    Attributes:
        year: The year to filter by
        season: The season to filter by
        status: The status to filter by
        media_type: The media type to filter by
    """

    year: Optional[int] = None
    season: Optional[Season] = None
    status: Optional[Status] = None
    media_type: Optional[MediaType] = None


class FilterCapabilities(Flag):
    """A Flag class that describes the filter capabilities of a provider.
    Look [here](https://docs.python.org/3/library/enum.html#enum.Flag) to learn how to use this.

    Attributes:
        YEAR: The provider is able to filter by year.
        SEASON: The provider is able to filter by season.
        STATUS: The provider is able to filter by status of anime.
        MEDIA_TYPE: The provider is able to filter by media type of anime.
        NO_QUERY: The provider accepts a empty query, this is useful if you
            want to for example get all anime in a specific season, you do not
            want to provide a query for that because then you will only get
            shown the anime in that specific season that match the query. If a provider
            supports `NO_QUERY` it means that if you search without query you get all available
            anime in its database.
        ALL: The provider supports all of the capabilities above.
    """

    YEAR = auto()
    SEASON = auto()
    STATUS = auto()
    MEDIA_TYPE = auto()
    NO_QUERY = auto()
    ALL = YEAR | SEASON | STATUS | MEDIA_TYPE | NO_QUERY


class BaseFilter(ABC):
    def __init__(self, request: "Request"):
        self._request = request

    @abstractmethod
    def _apply_query(self, query: str): ...

    @abstractmethod
    def _apply_year(self, year: int): ...

    @abstractmethod
    def _apply_season(self, season: Season): ...

    @abstractmethod
    def _apply_status(self, status: Status): ...

    @abstractmethod
    def _apply_media_type(self, media_type: MediaType): ...

    def apply(self, query: str, filters: Filters) -> "Request":
        self._apply_query(query)

        for filter in fields(filters):
            value = getattr(filters, filter.name)
            if not value:
                continue

            try:
                func = self.__getattribute__(f"_apply_{filter.name}")
                func(value)
            except ValueError:
                pass

        return self._request
