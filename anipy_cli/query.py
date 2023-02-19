import requests
import re
from bs4 import BeautifulSoup

from anipy_cli.misc import loc_err, response_err, error, print_names
from anipy_cli.colors import colors, cinput
from anipy_cli.config import Config

base_url = Config().gogoanime_url


class query:
    """
    Class to get query results
    from a search parameter.
    Takes an empty entry or one
    with fields filled.
    """

    def __init__(self, search_param, entry) -> None:
        self.entry = entry
        self.search_url = base_url + f"/search.html?keyword={search_param}"
        r = requests.get(self.search_url)
        response_err(r, self.search_url)
        self.soup = BeautifulSoup(r.content, "html.parser")

    def get_pages(self):
        """Get count of result pages of query"""
        pages = self.soup.find_all(
            "a", attrs={"data-page": re.compile(r"^ *\d[\d ]*$")}
        )
        loc_err(pages, self.search_url, "page-count")
        pages = [x.get("data-page") for x in pages]
        try:
            self.pages = int(pages[-1])
        except:
            self.pages = 1

    def get_links(self):
        """
        Get all category links and names of a query
        and returns them.
        """
        self.get_pages()
        self.links = []
        self.names = []
        for i in range(self.pages):
            req_link = self.search_url + f"&page={i + 1}"
            r = requests.get(req_link)
            response_err(r, req_link)
            self.soup = BeautifulSoup(r.content, "html.parser")

            for link in self.soup.find_all("p", attrs={"class": "name"}):
                name_lower = link.text.lower()
                if len(Config().anime_types) == 1:
                    if "sub" in Config().anime_types and "(dub)" in name_lower:
                        continue
                    elif "dub" in Config().anime_types and "(dub)" not in name_lower:
                        continue

                loc_err(link, req_link, "query results")
                self.names.append(link.text.replace("\n", ""))
                a_tag = link.findChildren("a", recursive=False)
                self.links.append(a_tag[0].get("href"))

        if not self.links:
            return 0
        else:
            return self.links, self.names

    def pick_show(self, cancelable=False):
        """
        Cli Function that
        Lets you pick a show from
        yout query, filles the category_url
        field from the entry and returns it.
        """
        print_names(self.names)
        if cancelable:
            print(f"{colors.GREEN}[C] {colors.YELLOW} Cancel.")
        while True:
            inp = cinput("Enter Number: ", colors.CYAN)
            try:
                self.entry.category_url = base_url + self.links[int(inp) - 1]
                self.entry.show_name = self.names[int(inp) - 1]
                break
            except:
                if cancelable and inp.lower() == "c":
                    return False
                error("Invalid Input")

        return self.entry
