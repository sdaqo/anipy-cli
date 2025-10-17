import functools
from typing import TYPE_CHECKING, List

from base64 import b64encode

from pathlib import Path

from anipy_api.provider import (
    BaseProvider,
    ProviderInfoResult,
    ProviderSearchResult,
    ProviderStream,
    LanguageTypeEnum,
    Episode
)
from anipy_api.provider.filter import (
    FilterCapabilities,
    Filters,
)

if TYPE_CHECKING:
    from anipy_api.provider import Episode
    from typing import Dict


class NativeProvider(BaseProvider):
    """For detailed documentation have a look
    at the [base class][anipy_api.provider.base.BaseProvider].

    Attributes:
        NAME: native 
        BASE_URL: ~/Videos 
        FILTER_CAPS: NO_QUERY
    """

    NAME: str = "native"
    BASE_URL: str = "~/Videos"
    FILTER_CAPS: FilterCapabilities = FilterCapabilities.NO_QUERY
    
    @staticmethod
    @functools.lru_cache()
    def _get_anime_tree(path: Path):
        anime_tree: Dict = {}

        for root, dirs, files in path.walk():
            for f in files:
                f = root / f
                if f.suffix not in [
                    ".mkv", ".mp4",
                    ".webm", ".flv",
                    ".ts", ".avi", ".mov"
                ]:
                    continue

                path_wo_root = Path(str(f).replace(str(path), ""))
                name = " ".join([p.name for p in path_wo_root.parents])
                keyname = b64encode(name.encode()).decode()
                
                if keyname in anime_tree:
                    anime_tree[keyname]["eps"].append(f)
                else:
                    anime_tree[keyname] = {"eps": [f], "name": name}

        return anime_tree

    def get_search(
        self, query: str, filters: "Filters" = Filters()
    ) -> List[ProviderSearchResult]:
        anime_tree = self._get_anime_tree(Path(self.BASE_URL))

        matches = [] 
        for k, i in anime_tree.items():
            if not query.lower() in i["name"].lower():
                continue

            matches.append(
                ProviderSearchResult(
                    identifier=k,
                    name=i["name"],
                    languages={LanguageTypeEnum.SUB}
                )
            )

        return matches

    def get_episodes(self, identifier: str, lang: LanguageTypeEnum) -> List[Episode]:
        anime_tree = self._get_anime_tree(Path(self.BASE_URL))
        
        episodes = range(1, len(anime_tree[identifier]["eps"]) + 1)

        return list(episodes)

    def get_info(self, identifier: str) -> "ProviderInfoResult":
        anime_tree = self._get_anime_tree(Path(self.BASE_URL))
        anime = anime_tree[identifier]

        return ProviderInfoResult(
            name=anime["name"]
        )

    def get_video(
        self, identifier: str, episode: Episode, lang: LanguageTypeEnum
    ) -> List[ProviderStream]:
        anime_tree = self._get_anime_tree(Path(self.BASE_URL))
        anime = anime_tree[identifier]

        episode_file = sorted(anime["eps"])[int(episode) - 1]
        
        return [ProviderStream(
            url=episode_file,
            resolution=0,
            episode=episode,
            language=LanguageTypeEnum.SUB
        )]
