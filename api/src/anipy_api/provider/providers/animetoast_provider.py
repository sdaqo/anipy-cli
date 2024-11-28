import math
import re
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List
from urllib.parse import urljoin

import m3u8
from bs4 import BeautifulSoup
from requests import Request

from anipy_api.error import BeautifulSoupLocationError
from anipy_api.provider import (
    BaseProvider,
    LanguageTypeEnum,
    ProviderInfoResult,
    ProviderSearchResult,
    ProviderStream,
)
from anipy_api.provider.filter import (
    BaseFilter,
    FilterCapabilities,
    Filters,
    MediaType,
    Season,
    Status,
)

from anipy_api.provider.utils import safe_attr

if TYPE_CHECKING:
    from anipy_api.provider import Episode


class AnimetoastFilter(BaseFilter):
    def _apply_query(self, query: str):
        self._request.params.update({"s": query})

    def _apply_year(self, year: int):
        self._request.params.update({"year": year})

    def _apply_season(self, season: Season):
        # mapping = {v: k.capitalize() for k, v in Season._member_map_.items()}
        # self._request.params.update({"season": mapping[season]})
        ...

    def _apply_status(self, status: Status):
        # mapping = {
        #     Status.COMPLETED: "Finished Airing",
        #     Status.UPCOMING: "Not yet aired",
        #     Status.ONGOING: "Currently Airing",
        # }
        # self._request.params.update({"status": mapping[status]})
        ...

    def _apply_media_type(self, media_type: MediaType):
        # mapping = {
        #     MediaType.TV: "TV",
        #     MediaType.SPECIAL: "Special",
        #     MediaType.MOVIE: "Movie",
        #     MediaType.OVA: "OVA",
        #     MediaType.ONA: "ONA",
        #     MediaType.MUSIC: "Music",
        # }
        # self._request.params.update({"type": mapping[media_type]})
        ...


class AnimetoastProvider(BaseProvider):
    """For detailed documentation have a look
    at the [base class][anipy_api.provider.base.BaseProvider].

    Attributes:
        NAME: animetoast
        BASE_URL: https://animetoast.cc
        FILTER_CAPS: YEAR, NO_QUERY
    """

    NAME: str = "animetoast"
    BASE_URL: str = "https://www.animetoast.cc"
    FILTER_CAPS: FilterCapabilities = (
        FilterCapabilities.YEAR | FilterCapabilities.NO_QUERY
    )

    def get_search(
        self, query: str, filters: "Filters" = Filters()
    ) -> List[ProviderSearchResult]:
        req = Request("GET", f"{self.BASE_URL}/")
        req = AnimetoastFilter(req).apply(query, filters)

        res = self._request_page(req)
        soup = BeautifulSoup(res.content, "html.parser")

        pages = safe_attr(soup.find("span", attrs={"class": "pages"}), "text")
        if pages is not None:
            pages = re.search(r"[0-9]+$", pages)
            if pages is not None:
                pages = min(
                    int(pages.group(0)), 3
                )  # max 3 pages to not flood site with requests
        else:
            pages = 1  # fall back to one page

        results: Dict[str, ProviderSearchResult] = {}

        for p in range(pages):
            if p != 0:  # do not request page one twice!
                req = Request("GET", f"{self.BASE_URL}/page/{p + 1}/")
                req = AnimetoastFilter(req).apply(query, filters)
                res = self._request_page(req)
                soup = BeautifulSoup(res.content, "html.parser")
            links = soup.find_all("div", "item-thumbnail")
            if links is None:
                raise BeautifulSoupLocationError("query results", res.url)

            for link in links:
                link = link.findChildren("a", recursive=False)[0]
                if link is None:
                    continue

                name = (
                    link.get("title")
                    .replace("\n", "")
                    .replace(": ", " - ")
                    .replace(":", "-")
                    .replace("?", "")
                    .replace("|", "")
                )  # make name windows conform

                name = name.removesuffix(" Sub")
                name = name.removesuffix(" Dub")

                # remove these to keep Ger suffix
                name = name.removesuffix(" Ger")
                name = name.removesuffix(" Ger")

                identifier = Path(link.get("href")).name

                if "-dub" in identifier and not identifier.endswith("-sub"):
                    identifier = identifier[: identifier.find("-dub")]
                    # identifier = identifier.removesuffix("-dub")
                    if identifier not in results:
                        results[identifier] = ProviderSearchResult(
                            identifier, name, languages={LanguageTypeEnum.DUB}
                        )
                    else:
                        results[identifier].languages.add(LanguageTypeEnum.DUB)
                else:
                    identifier = identifier.removesuffix("-sub")
                    if identifier not in results:
                        results[identifier] = ProviderSearchResult(
                            identifier, name, languages={LanguageTypeEnum.SUB}
                        )
                    else:
                        results[identifier].languages.add(LanguageTypeEnum.SUB)

        return list(results.values())

    def get_episodes(self, identifier: str, lang: LanguageTypeEnum) -> List["Episode"]:
        url = f"{self.BASE_URL}/{identifier}-sub"
        if lang == LanguageTypeEnum.DUB:
            url = f"{self.BASE_URL}/{identifier}-dub"
        req = Request("GET", url)
        res = self._request_page(req)
        soup = BeautifulSoup(res.content, "html.parser")
        tab = self._get_voe_tab(soup)
        if tab is None:
            raise BeautifulSoupLocationError("provider results", res.url)
        episodes = tab.findChildren("a")
        eps = []
        if "-" in episodes[0].text:  # episodes in ranges
            i = 0
            ep_start_indexes, ep_ranges = self._get_ep_ranges(episodes)
            for ep_range_start, ep_range in zip(ep_start_indexes, ep_ranges):
                if len(ep_range) == 0 or len(ep_start_indexes) == 1:
                    # propably ends with '-' go deeper!
                    # len(ep_start_indexes) == 1 to get a more accurate list of episodes if there is only one range (e.g. to catch .5 episodes)
                    url = self._get_embed_player_url(episodes[i].get("href"))
                    if url != "":
                        req = Request("GET", url)
                        res = self._request_page(req)
                        soup = BeautifulSoup(res.content, "html.parser")
                        tab = self._get_voe_tab(soup)
                        if tab is None:
                            raise BeautifulSoupLocationError(
                                "provider results", res.url
                            )
                        episodes = tab.findChildren("a")
                        ep_range = self._get_eps_in_range(episodes, ep_range_start)
                eps.extend(ep_range)
                i += 1
        else:  # episodes directly in list
            eps.extend(self._get_eps_in_range(episodes))

        return eps

    def get_info(self, identifier: str) -> "ProviderInfoResult":
        url = f"{self.BASE_URL}/{identifier}"
        req = Request("GET", url)
        res = self._request_page(req)
        soup = BeautifulSoup(res.content, "html.parser")

        data_map = {
            "name": None,
            "image": None,
            "genres": [],
            "synopsis": None,
            "release_year": None,
            "status": None,
            "alternative_names": [],
        }

        name = safe_attr(soup.find("meta", attrs={"property": "og:title"}), "content")
        if name is not None:
            name = name.removesuffix(" Sub")
            name = name.removesuffix(" Dub")

            # remove these to keep Ger suffix
            name = name.removesuffix(" Ger")
            name = name.removesuffix(" Ger")
        data_map["name"] = name

        prev = soup.find("div", attrs={"class": "multi_link-area"})
        if prev is None:
            return ProviderInfoResult(**data_map)

        data_map["image"] = safe_attr(prev.find_next("img"), "src")

        sections = prev.find_next_siblings("p")

        for sec in sections:
            sec.ne
            strong = sec.find("strong")
            if strong is not None:
                if strong.text.lower() == "genre:":
                    # get genre
                    data_map["genres"] = strong.next_sibling.text.replace(
                        " ", ""
                    ).split(",")
                elif strong.text.lower() == "season start:":
                    # get season (year)
                    year = re.search(r"[0-9]+", strong.next_sibling.text)
                    if year is not None:
                        data_map["release_year"] = year.group(0)
                elif strong.text == name:
                    # get alternate names
                    for sibling in strong.next_siblings:
                        alt_name = sibling.text.strip().replace("\n", "")
                        if alt_name != "":
                            data_map["alternative_names"].append(alt_name)

        return ProviderInfoResult(**data_map)

    def get_video(
        self, identifier: str, episode: "Episode", lang: LanguageTypeEnum
    ) -> List["ProviderStream"]:
        url = f"{self.BASE_URL}/{identifier}-sub"
        if lang == LanguageTypeEnum.DUB:
            url = f"{self.BASE_URL}/{identifier}-dub"
        req = Request("GET", url)
        res = self._request_page(req)
        soup = BeautifulSoup(res.content, "html.parser")

        tab = self._get_voe_tab(soup)
        if tab is None:
            raise BeautifulSoupLocationError("provider results", res.url)
        episodes = tab.findChildren("a")
        if "-" in episodes[0].text:
            # TODO: .5 episodes do not work in ranges (works if only one range exists)
            # find correct range
            range_idx = -1
            start_indexes, ranges = self._get_ep_ranges(
                episodes
            )  # inefficient but simplifies code
            for i in range(len(start_indexes)):
                if episode in ranges[i]:
                    range_idx = i
                    break
            range_url = self._get_embed_player_url(episodes[range_idx].get("href"))
            if range_url == "":
                raise BeautifulSoupLocationError("player", res.url)
            req = Request("GET", range_url)
            res = self._request_page(req)
            soup = BeautifulSoup(res.content, "html.parser")

            tab = self._get_voe_tab(soup)
            if tab is None:
                raise BeautifulSoupLocationError("provider results", res.url)
            episodes = tab.findChildren("a")
            return self._extract_streams_from_ep(
                episodes, lang, episode, start_indexes[range_idx]
            )
        else:
            return self._extract_streams_from_ep(episodes, lang, episode)

    def _get_voe_tab(self, soup):
        tabs = soup.find_all("a", attrs={"data-toggle": "tab"})
        if tabs is None:
            return None
        tab_id = None
        for tab in tabs:
            if tab.text.lower() == "voe":
                tab_id = tab.get("href")[1:]
                break
        if tab_id is None:
            return None
        tab = soup.find("div", attrs={"id": tab_id})
        return tab

    def _get_eps_in_range(self, episodes, override_start_ep: int = -1) -> List[int]:
        eps = []
        # skip to range (needed because of weird website design)
        for i in range(len(episodes)):
            if "current-link" in episodes[i].attrs["class"]:
                episodes = episodes[i:]
                break
        ep_num = 0
        for i in range(len(episodes)):
            if override_start_ep < 1:
                match_num = re.search(r"[0-9]+", episodes[i].text)
                if match_num is not None:
                    ep_num = match_num.group(0)
                else:
                    ep_num = int(ep_num) + 1  # workaround if last episode has no number
            else:
                ep_num = override_start_ep + i
            eps.append(int(ep_num))
        return eps

    def _get_ep_ranges(self, episodes) -> tuple[List[int], List[List[int]]]:
        start_indexes = []
        ranges = []
        for ep_range in episodes:
            match_range = re.search(
                r"([0-9]+)-([0-9]+(.[0-9])?)?", ep_range.text
            )  # catch .5 episode if at the end TODO: rewrite to support .5 episodes everywhere
            if match_range is None:
                continue  # no range found

            start_indexes.append(int(match_range.group(1)))

            if len(match_range.groups()) == 1 or match_range.group(2) is None:
                ranges.append([])
                continue  # case where ep ranges do not provide the end e.g. (S10E500-)

            ranges.append(
                range(
                    int(match_range.group(1)),
                    math.ceil(float(match_range.group(2))) + 1,
                )
            )
        return (start_indexes, ranges)

    def _get_embed_player_url(self, url) -> str:
        req = Request("GET", f"{url}")
        res = self._request_page(req)
        soup = BeautifulSoup(res.content, "html.parser")
        player = soup.find("div", attrs={"id": "player-embed"})
        if player is None:
            return ""
        return player.findChildren("a")[0].get("href")

    def _extract_streams_from_ep(
        self, episodes, lang, episode: "Episode", range_start=1
    ) -> List["ProviderStream"]:
        # skip to range (needed because of weird website design)
        for i in range(len(episodes)):
            if "current-link" in episodes[i].attrs["class"]:
                episodes = episodes[i:]
                break

        stream_url = episodes[episode - range_start].get("href")
        i = 0
        while (
            self.BASE_URL in stream_url or i == 0
        ):  # make sure we grab the provider and not an animetoast link - happens in rare cases
            new_stream_url = self._get_embed_player_url(stream_url)
            if new_stream_url == "" or i > 2:
                break  # try to extract from last given url anyways
            stream_url = new_stream_url
            i += 1  # prevent infinite loop
        req = Request("GET", f"{stream_url}")
        res = self._request_page(req)
        extracted_streams = self._extract_streams(res, episode, lang)
        if len(extracted_streams) == 0:
            # video may be behind a redirect
            stream_url = re.search(r"window\.location\.href = '(.*)'", res.text)
            if stream_url is not None:
                req = Request("GET", f"{stream_url.group(1)}")
                res = self._request_page(req)
                return self._extract_streams(res, episode, lang)
        return extracted_streams

    def _extract_streams(self, res, episode: "Episode", lang) -> List["ProviderStream"]:
        streams = []
        stream_url = re.search(r"prompt\(\"Node\", \"(https:\/\/.*)\"", res.text)
        if stream_url is not None:
            content = m3u8.load(stream_url.group(1))
            if len(content.playlists) == 0:
                streams.append(ProviderStream(stream_url, 720, episode, lang))
            else:
                for playlist in content.playlists:
                    streams.append(
                        ProviderStream(
                            url=urljoin(content.base_uri, playlist.uri),
                            resolution=playlist.stream_info.resolution[1],
                            episode=episode,
                            language=lang,
                        )
                    )

        return streams
