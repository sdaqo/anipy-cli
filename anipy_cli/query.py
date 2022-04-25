import requests
import re
from bs4 import BeautifulSoup

from .misc import loc_err, response_err, error, print_names
from .colors import colors
from . import config

base_url = config.gogoanime_url


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
                loc_err(link, req_link, "query results")
                self.names.append(link.text)
                a_tag = link.findChildren("a", recursive=False)
                self.links.append(a_tag[0].get("href"))

        if not self.links:
            error("no search results")
            return 0
        else:
            return self.links, self.names

    def pick_show(self):
        """
        Cli Function that
        Lets you pick a show from
        yout query, filles the category_url
        field from the entry and returns it.
        """
        print_names(self.names)
        while True:
            inp = input("Enter Number: " + colors.CYAN)
            try:
                self.entry.category_url = base_url + self.links[int(inp) - 1]
                self.entry.show_name = self.names[int(inp) - 1]
                break
            except:
                error("Invalid Input")

        return self.entry
