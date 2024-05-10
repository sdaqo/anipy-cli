from typing import TYPE_CHECKING, Optional, Set, Union, List

from anipy_api.provider import Episode, list_providers

if TYPE_CHECKING:
    from anipy_api.locallist import LocalListEntry
    from anipy_api.provider import (
        BaseProvider,
        LanguageTypeEnum,
        ProviderSearchResult,
        ProviderInfoResult,
        ProviderStream,
    )


class Anime:
    """A wrapper class that represents an anime, it is pretty useful, but you
    can also just use the [Provider][anipy_api.provider.base.BaseProvider] without the wrapper.

    Args:
        provider: The provider from which the identifier was retrieved
        name: The name of the Anime
        identifier: The identifier of the Anime
        languages: Supported Language types of the Anime

    Attributes:
        provider: The from which the Anime comes from
        name: The name of the Anime
        identifier: The identifier of the Anime
        languages: Set of supported Language types of the Anime
    """

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
    def from_local_list_entry(entry: "LocalListEntry") -> "Anime":
        """Get Anime object from [LocalListEntry][anipy_api.locallist.LocalListEntry]

        Args:
            entry: The local list entry

        Returns:
            Anime Object
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
        self.provider: "BaseProvider" = provider
        self.name: str = name
        self.identifier: str = identifier
        self.languages: Set["LanguageTypeEnum"] = languages

    def get_episodes(self, lang: "LanguageTypeEnum") -> List["Episode"]:
        """Get a list of episodes from the Anime.

        Args:
            lang: Language type that determines if episodes are searched
                for the dub or sub version of the Anime. Use the `languages`
                attribute to get supported languages for this Anime.

        Returns:
            List of Episodes
        """
        return self.provider.get_episodes(self.identifier, lang)

    def get_info(self) -> "ProviderInfoResult":
        """Get information about the Anime.

        Returns:
            ProviderInfoResult object
        """
        return self.provider.get_info(self.identifier)

    def get_video(
        self,
        episode: Episode,
        lang: "LanguageTypeEnum",
        preferred_quality: Optional[Union[str, int]] = None,
    ) -> "ProviderStream":
        """Get a video stream for the specified episode, the quality to return
        is determined by the `preferred_quality` argument or if this is not
        defined by the best quality found. To get a list of streams use
        [get_videos][anipy_api.anime.Anime.get_videos].

        Args:
            episode: The episode to get the stream for
            lang: Language type that determines if streams are searched for
                the dub or sub version of the Anime. Use the `languages`
                attribute to get supported languages for this Anime.
            preferred_quality: This may be a integer (e.g. 1080, 720 etc.)
                or the string "worst" or "best".

        Returns:
            A stream
        """
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

    def get_videos(
        self, episode: Episode, lang: "LanguageTypeEnum"
    ) -> List["ProviderStream"]:
        """Get a list of video streams for the specified Episode.

        Args:
            episode: The episode to get the streams for
            lang: Language type that determines if streams are searched for
                the dub or sub version of the Anime. Use the `languages`
                attribute to get supported languages for this Anime.

        Returns:
            A list of streams sorted by quality
        """
        streams = self.provider.get_video(self.identifier, episode, lang)
        streams.sort(key=lambda s: s.resolution)

        return streams

    def __repr__(self) -> str:
        available_langs = "/".join(
            [lang.value.capitalize()[0] for lang in self.languages]
        )
        return f"{self.name} ({available_langs})"

    def __hash__(self) -> int:
        return hash(self.provider.NAME + self.identifier)
