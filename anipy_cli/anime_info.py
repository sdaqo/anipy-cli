from datetime import date
import asyncio
import kitsu_extended


class AnimeInfo:
    """
    Anime Info Class.
    Provide methods for finding anime using the Kitsu API
    """

    def __init__(self):
        self.client = kitsu_extended.Client()
        assert self.client is not None, "Failed to initialize kitsu client."
        self.season_names = {"spring", "summer", "fall", "winter"}

        pass

    def get_anime_by_season(self, season_year=date.today().year, season_name="spring"):
        """
        Returns all anime of given season

        :param season_year: Year of Season
        :type season_year: int
        :param season_name: name of the season (spring,summer,fall,winter)
        :type season_name: str
        :return: list of Anime
        :rtype: list
        """

        season_name = season_name.lower()

        assert (
            season_name in self.season_names
        ), f"Unknown season name. Supported: {', '.join(list(self.season_names))}"

        search_results = self.search_anime(season=season_name, season_year=season_year)

        return search_results

    def search_anime(self, *, anime_search_string: str = "", **filters) -> list:
        """
        Wrapper method for searching anime to get around result limit of 20

        :param anime_search_string: anime to search for
        :type anime_search_string: str
        :param filters: Additional filter arguments | reference: https://kitsu.docs.apiary.io/#reference/anime/anime/
        :type filters: **kwargs
        :return: List of anime search results
        :rtype: list
        """
        offset = 0
        search_results = []
        search_result = True
        loop = asyncio.get_event_loop()
        while search_result:
            search_result = loop.run_until_complete(
                self.client.search_anime(
                    query=anime_search_string, limit=20, offset=offset, **filters
                )
            )
            if search_result:
                search_results += search_result

            offset += 20
        loop.run_until_complete(self.client.close())

        search_results.sort(key=lambda x: (x.average_rating or 0.0), reverse=True)

        return search_results
