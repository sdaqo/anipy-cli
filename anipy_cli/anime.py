from typing import TYPE_CHECKING, Optional, Union

from anipy_cli.provider import (
    BaseProvider,
    Episode,
    ProviderSearchResult,
    list_providers,
)
if TYPE_CHECKING:
    from anipy_cli.history import HistoryEntry
    from anipy_cli.seasonal import SeasonalEntry

class Anime:
    @staticmethod
    def from_search_result(
        provider: BaseProvider, result: ProviderSearchResult
    ) -> "Anime":
        return Anime(provider, result.name, result.identifier)

    @staticmethod
    def from_history_entry(entry: "HistoryEntry") -> "Anime":
        provider = next(filter(lambda x: x.NAME == entry.provider, list_providers()))
        return Anime(provider(), entry.name, entry.identifier)

    @staticmethod
    def from_seasonal_entry(entry: "SeasonalEntry") -> "Anime":
        provider = next(filter(lambda x: x.NAME == entry.provider, list_providers()))
        return Anime(provider(), entry.name, entry.identifier)

    def __init__(self, provider: BaseProvider, name: str, identifier: str):
        self.provider = provider
        self.name = name
        self.identifier = identifier

    def get_episodes(self):
        return self.provider.get_episodes(self.identifier)

    def get_info(self):
        return self.provider.get_info(self.identifier)

    def get_video(self, episode: Episode, preferred_quality: Optional[Union[str, int]]):
        streams = self.provider.get_video(self.identifier, episode)
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
        return self.name
