from typing import TYPE_CHECKING, Optional, Set, Union

from anipy_api.provider import Episode, list_providers

if TYPE_CHECKING:
    from anipy_api.history import HistoryEntry
    from anipy_api.provider import BaseProvider, LanguageTypeEnum, ProviderSearchResult
    from anipy_api.seasonal import SeasonalEntry


class Anime:
    """A wrapper class that represents a Anime, it is pretty useful, but you
    can also just use the [Provider][anipy_api.provider] without the
    wrapper."""

    @staticmethod
    def from_search_result(
        provider: "BaseProvider", result: "ProviderSearchResult"
    ) -> "Anime":
        """Get Anime object from ProviderSearchResult.

        Args:
            provider: The provider from which the search result stems from
            result: The search result

        Returns:
            Anime object
        """
        return Anime(provider, result.name, result.identifier, result.languages)

    @staticmethod
    def from_history_entry(entry: "HistoryEntry") -> "Anime":
        """Get Anime object from [HistoryEntry][anipy_api.history.HistoryEntry]

        Args:
            entry: The history entry

        Returns:
            Anime Object
        """
        provider = next(filter(lambda x: x.NAME == entry.provider, list_providers()))
        return Anime(provider(), entry.name, entry.identifier, entry.languages)

    @staticmethod
    def from_seasonal_entry(entry: "SeasonalEntry") -> "Anime":
        """Get Anime object from
        [SeasonalEntry][anipy_api.seasonal.SeasonalEntry]

        Args:
            entry:

        Returns:
        """
        provider = next(filter(lambda x: x.NAME == entry.provider, list_providers()))
        return Anime(provider(), entry.name, entry.identifier, entry.languages)

    def __init__(
        self,
        provider: "BaseProvider",
        name: str,
        identifier: str,
        languages: Set["LanguageTypeEnum"],
    ):
        self.provider = provider
        self.name = name
        self.identifier = identifier
        self.languages = languages

    def get_episodes(self, lang: "LanguageTypeEnum"):
        return self.provider.get_episodes(self.identifier, lang)

    def get_info(self):
        return self.provider.get_info(self.identifier)

    def get_video(
        self,
        episode: Episode,
        lang: "LanguageTypeEnum",
        preferred_quality: Optional[Union[str, int]] = None,
    ):
        streams = self.provider.get_video(self.identifier, episode, lang)
        streams.sort(key=lambda s: s.resolution)

        if preferred_quality == "worst":
            stream = streams[0]
        elif preferred_quality == "best":
            stream = streams[-1]
        elif preferred_quality is None:
            stream = streams[-1]
        else:
            stream = next(
                filter(lambda s: s.resolution == preferred_quality, streams), None
            )

            if stream is None:
                stream = streams[-1]

        return stream

    def __repr__(self) -> str:
        available_langs = "/".join([l.value.capitalize()[0] for l in self.languages])
        return f"{self.name} ({available_langs})"

    def __hash__(self) -> int:
        return hash(self.provider.NAME + self.identifier)
