from typing import Union, List, Optional
from dataclasses import dataclass

from anipy_cli.provider import BaseProvider, ProviderSearchResult, ProviderStream, Episode

class Anime():
    @staticmethod
    def from_search_results(provider: BaseProvider, results: List[ProviderSearchResult]) -> List["Anime"]:
        return [Anime(provider, x) for x in results]

    def __init__(self, provider: BaseProvider, anime: ProviderSearchResult):
        self.provider = provider
        self.identifier = anime.identifier
        self.name = anime.name

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
            stream = next(filter(lambda s: s.resolution == preferred_quality, streams), None)

            if stream is None:
                stream = streams[-1]

        return stream

    def __repr__(self) -> str:
        return self.name

