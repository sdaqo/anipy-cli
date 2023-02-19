from anipy_cli.colors import cprint, colors, cinput
from anipy_cli.misc import Entry, search_in_season_on_gogo, print_names
from anipy_cli.url_handler import epHandler, videourl
from anipy_cli.mal import MAL
from anipy_cli.seasonal import Seasonal
from anipy_cli.player import PlayerBaseType


def binge(ep_list, quality, player: PlayerBaseType, mode="", mal_class: MAL = None):
    """
    TODO: bruh what is this, let this accept a list of Entry
    Accepts ep_list like so:
        {"name" {'ep_urls': [], 'eps': [], 'category_url': }, "next_anime"...}
    """
    cprint(colors.RED, "To quit press CTRL+C")
    try:
        for i in ep_list:
            print(i)
            show_entry = Entry()
            show_entry.show_name = i
            show_entry.category_url = ep_list[i]["category_url"]
            show_entry.latest_ep = epHandler(show_entry).get_latest()
            for url, ep in zip(ep_list[i]["ep_urls"], ep_list[i]["eps"]):
                show_entry.ep = ep
                show_entry.embed_url = ""
                show_entry.ep_url = url
                cprint(
                    colors.GREEN,
                    "Fetching links for: ",
                    colors.END,
                    show_entry.show_name,
                    colors.RED,
                    f""" | EP: {
                    show_entry.ep
                    }/{
                    show_entry.latest_ep
                    }""",
                )

                url_class = videourl(show_entry, quality)
                url_class.stream_url()
                show_entry = url_class.get_entry()
                player.play_title(show_entry)
                player.wait()

                if mode == "seasonal":
                    Seasonal().update_show(
                        show_entry.show_name, show_entry.category_url, show_entry.ep
                    )
                elif mode == "mal":
                    mal_class.update_watched(show_entry.show_name, show_entry.ep)

    except KeyboardInterrupt:
        player.kill_player()


def get_season_searches(gogo=True):
    searches = []
    selected = []
    season_year = None
    season_name = None
    while not season_year:
        try:
            season_year = int(cinput(colors.CYAN, "Season Year: "))
        except ValueError:
            print("Please enter a valid year.\n")

    while not season_name:
        season_name_input = cinput(
            colors.CYAN, "Season Name (spring|summer|fall|winter): "
        )
        if season_name_input.lower() in ["spring", "summer", "fall", "winter"]:
            season_name = season_name_input

        else:
            cprint(colors.YELLOW, "Please enter a valid season name.\n")

    if gogo:
        anime_in_season = search_in_season_on_gogo(season_year, season_name)

    else:
        anime_in_season = MAL().get_seasonal_anime(season_year, season_name)

    cprint("Anime found in {} {} Season: ".format(season_year, season_name))
    cprint(
        colors.CYAN,
        "Anime found in ",
        colors.GREEN,
        season_year,
        colors.CYAN,
        " ",
        colors.YELLOW,
        season_name,
        colors.CYAN,
        " Season: ",
    )
    anime_names = []
    for anime in anime_in_season:
        if gogo:
            anime_names.append(anime["name"])

        else:
            anime_names.append(anime["node"]["title"])

    print_names(anime_names)
    selection = cinput(colors.CYAN, "Selection: (e.g. 1, 1  3 or 1-3) \n>> ")
    if selection.__contains__("-"):
        selection_range = selection.strip(" ").split("-")
        for i in range(int(selection_range[0]) - 1, int(selection_range[1]) - 1, 1):
            selected.append(i)

    else:
        for i in selection.lstrip(" ").rstrip(" ").split(" "):
            selected.append(int(i) - 1)

    for value in selected:
        searches.append(anime_in_season[int(value)])
    return searches
