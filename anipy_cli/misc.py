import os
import requests
import sys
import json
from bs4 import BeautifulSoup
from dataclasses import dataclass

from . import config
from .colors import colors

options = [
    colors.GREEN + "[n] " + colors.END + "Next Episode",
    colors.GREEN + "[p] " + colors.END + "Previous Episode",
    colors.GREEN + "[r] " + colors.END + "Replay episode",
    colors.GREEN + "[s] " + colors.END + "Select episode",
    colors.GREEN + "[h] " + colors.END + "History selection",
    colors.GREEN + "[a] " + colors.END + "Search for Anime",
    colors.GREEN + "[i] " + colors.END + "Print Video Info",
    colors.GREEN + "[q] " + colors.END + "Quit",
]


seasonal_options = [
    colors.GREEN + "[a] " + colors.END + "Add Anime",
    colors.GREEN + "[e] " + colors.END + "Delete one anime from seasonals",
    colors.GREEN + "[l] " + colors.END + "List animes in seasonals file",
    colors.GREEN + "[d] " + colors.END + "Download newest episodes",
    colors.GREEN + "[w] " + colors.END + "Binge watch newest episodes",
    colors.GREEN + "[q] " + colors.END + "Quit",
]


@dataclass
class entry:
    """
    This is the class that saves
    metadata about a show. It is required
    by all classes, it is a essential
    part of this script.
    """

    show_name: str = ""
    category_url: str = ""
    ep_url: str = ""
    embed_url: str = ""
    stream_url: str = ""
    ep: int = 0
    latest_ep: int = 0
    quality: str = ""


def clear_console():
    os.system("cls" if os.name == "nt" else "clear")


def error(error: str) -> None:
    """
    Error function for better error handling,
    that takes an error and prints it to stderr.
    """
    sys.stderr.write(colors.ERROR + "anipy-cli: error: " + error + colors.END + "\n")


def response_err(req, link) -> None:
    """
    Function that checks if a requsted
    was succesfull.
    """
    if req.ok:
        pass
    else:
        error(
            f"requsted url not avalible/blocked: {link}: response-code: {req.status_code}"
        )
        sys.exit()


def loc_err(soup, link: str, element: str) -> None:
    """
    Function that checks if beautifulsoup
    could locate a element.
    """
    if soup == None:
        error(f"could not locate {element}: {link}")
        sys.exit()


def keyboard_inter() -> None:
    print(colors.ERROR + "\nanipy-cli: error: interrupted")
    sys.exit()


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
                config.user_files_path.mkdir(exist_ok=True)
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
    list oof names and prints
    them to the terminal.
    """
    for number, value in enumerate(names, 1):
        color = ""
        if number % 2 == 0:
            color = colors.YELLOW

        print(
            colors.GREEN + f"[{number}]" + colors.END + f"{color} {value}" + colors.END
        )


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
