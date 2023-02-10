import os
import requests
import sys
import json
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import Union

from .config import Config
from .colors import colors, color, cprint

options = [
    color(colors.GREEN, "[n] ") + "Next Episode",
    color(colors.GREEN, "[p] ") + "Previous Episode",
    color(colors.GREEN, "[r] ") + "Replay episode",
    color(colors.GREEN, "[s] ") + "Select episode",
    color(colors.GREEN, "[h] ") + "History selection",
    color(colors.GREEN, "[a] ") + "Search for Anime",
    color(colors.GREEN, "[i] ") + "Print Video Info",
    color(colors.GREEN, "[d] ") + "Download Episode",
    color(colors.GREEN, "[q] ") + "Quit",
]


seasonal_options = [
    color(colors.GREEN, "[a] ") + "Add Anime",
    color(colors.GREEN, "[e] ") + "Delete one anime from seasonals",
    color(colors.GREEN, "[l] ") + "List anime in seasonals file",
    color(colors.GREEN, "[d] ") + "Download newest episodes",
    color(colors.GREEN, "[w] ") + "Binge watch newest episodes",
    color(colors.GREEN, "[q] ") + "Quit",
]

mal_options = [
    color(colors.GREEN, "[a] ") + "Add Anime",
    color(colors.GREEN, "[e] ") + "Delete one anime from mal list",
    color(colors.GREEN, "[l] ") + "List anime in mal list",
    color(colors.GREEN, "[m] ") + "Manually Map MAL anime to gogo Link",
    color(colors.GREEN, "[s] ") + "Sync MAL list into seasonals",
    color(colors.GREEN, "[b] ") + "Sync seasonals into MAL list",
    color(colors.GREEN, "[d] ") + "Download newest episodes",
    color(colors.GREEN, "[x] ") + "Download all episodes",
    color(colors.GREEN, "[w] ") + "Binge watch newest episodes",
    color(colors.GREEN, "[q] ") + "Quit",
]


@dataclass
class entry:
    """
    This is the class that saves
    metadata about a show. It is required
    by all classes, it is an essential
    part of this script.
    """

    show_name: str = ""
    category_url: str = ""
    ep_url: str = ""
    embed_url: str = ""
    stream_url: str = ""
    ep: Union[int, float] = 0
    latest_ep: Union[int, float] = 0
    quality: str = ""


def clear_console():
    os.system("cls" if os.name == "nt" else "clear")


def error(error: str) -> None:
    """
    Error function for better error handling,
    that takes an error and prints it to stderr.
    """
    sys.stderr.write(color(colors.ERROR, "anipy-cli: error: " + error) + "\n")


def response_err(req, link) -> None:
    """
    Function that checks if a request
    was succesfull.
    """
    if req.ok:
        pass
    else:
        error(
            f"requested url not available/blocked: {link}: response-code: {req.status_code}"
        )
        sys.exit()


def loc_err(soup, link: str, element: str) -> None:
    """
    Function that checks if beautifulsoup
    could locate an element.
    """
    if soup == None:
        error(f"could not locate {element}: {link}")
        sys.exit()


def keyboard_inter() -> None:
    cprint(colors.ERROR, "\nanipy-cli: error: interrupted")
    sys.exit()


def parsenum(n: str):
    """
    Parse String to either
    int or float.
    """

    try:
        return int(n)
    except ValueError:
        return float(n)


def read_json(path):
    """
    Read a json file, if
    it doesn't exist create it,
    along with user_files folder.
    """
    while True:
        try:
            with open(path, "r") as data:
                json_data = json.load(data)
            break

        except FileNotFoundError:
            try:
                Config().user_files_path.mkdir(exist_ok=True, parents=True)
                path.touch(exist_ok=True)
                # avoids error on empty json file
                with path.open("a") as f:
                    f.write("{}")
                continue

            except PermissionError:
                error(f"Unable to create {path} due to permissions.")
                sys.exit()

    return json_data


def print_names(names):
    """
    Cli function that takes a
    list of names and prints
    them to the terminal.
    """
    for number, value in enumerate(names, 1):
        value_color = colors.END
        if number % 2 == 0:
            value_color = colors.YELLOW

        cprint(colors.GREEN, f"[{number}] ", value_color, value)


def get_anime_info(category_url: str) -> dict:
    """
    Get metadata about an anime.
    """
    r = requests.get(category_url)
    soup = BeautifulSoup(r.text, "html.parser")
    info_body = soup.find("div", {"class": "anime_info_body_bg"})
    image_url = info_body.find("img")["src"]
    other_info = info_body.find_all("p", {"class": "type"})
    info_dict = {
        "image_url": image_url,
        "type": other_info[0].text.replace("\n", "").replace("Type: ", ""),
        "synopsis": other_info[1].text.replace("\n", ""),
        "genres": [
            x["title"]
            for x in BeautifulSoup(str(other_info[2]), "html.parser").find_all("a")
        ],
        "release_year": other_info[3].text.replace("Released: ", ""),
        "status": other_info[4].text.replace("\n", "").replace("Status: ", ""),
    }

    return info_dict


def search_in_season_on_gogo(s_year, s_name):
    page = 1
    content = True
    gogo_anime_season_list = []
    while content:
        r = requests.get(
            f"{Config().gogoanime_url}/sub-category/{s_year}-{s_name}-anime",
            params={"page": page},
        )
        soup = BeautifulSoup(r.content, "html.parser")
        wrapper_div = soup.find("div", attrs={"class": "last_episodes"})
        try:
            anime_items = wrapper_div.findAll("li")
            for link in anime_items:
                link_a = link.find("p", attrs={"class": "name"}).find("a")
                name = link_a.get("title")
                gogo_anime_season_list.append(
                    {
                        "name": name,
                        "category_url": "{}{}".format(
                            Config().gogoanime_url, link_a.get("href")
                        ),
                    }
                )

        except AttributeError:
            content = False

        page += 1
    filtered_list = filter_anime_list_dub_sub(gogo_anime_season_list)

    return filtered_list


def filter_anime_list_dub_sub(gogo_anime_season_list):
    if "sub" not in Config().anime_types and "dub" in Config().anime_types:
        filtered_list = [
            x for x in gogo_anime_season_list if "(dub)" in x["name"].lower()
        ]

    elif "dub" not in Config().anime_types and "sub" in Config().anime_types:
        filtered_list = [
            x for x in gogo_anime_season_list if "(dub)" not in x["name"].lower()
        ]

    else:
        filtered_list = gogo_anime_season_list
    return filtered_list
