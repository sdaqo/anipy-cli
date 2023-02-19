from copy import deepcopy

from anipy_cli.arg_parser import CliArgs
from anipy_cli.config import Config
from anipy_cli.colors import cprint, colors
from anipy_cli.misc import Entry, parsenum
from anipy_cli.query import query
from anipy_cli.url_handler import videourl, epHandler
from anipy_cli.download import download
from anipy_cli.cli.util import get_season_searches
from anipy_cli.cli.clis.base_cli import CliBase


class DownloadCli(CliBase):
    def __init__(self, options: CliArgs, rpc_client=None):
        super().__init__(options, rpc_client)

        self.entry = Entry()
        self.show_entries = []
        self.dl_path = Config().download_folder_path
        if options.location:
            self.dl_path = options.location

    def print_header(self):
        cprint(colors.GREEN, "***Download Mode***")
        cprint(colors.GREEN, "Downloads are stored in: ", colors.END, str(self.dl_path))

    def take_input(self):
        is_season_search = False

        searches = []
        if (
            not self.options.no_season_search
            and input("Search MyAnimeList for anime in Season? (y|n): \n>> ") == "y"
        ):
            searches = get_season_searches()

        else:
            another = "y"
            while another == "y":
                searches.append(input("Search: "))
                another = input("Add another search: (y|n)\n")

        for search in searches:
            links = 0
            query_class = None
            if isinstance(search, dict):
                is_season_search = True
                links = [search["category_url"]]

            else:
                print("\nCurrent: ", search)
                query_class = query(search, self.entry)
                query_class.get_pages()
                links = query_class.get_links()

            if links == 0:
                self.exit("no search results")

            if is_season_search:
                self.entry = Entry()
                self.entry.show_name = search["name"]
                self.entry.category_url = search["category_url"]

            else:
                self.entry = query_class.pick_show()

            ep_class = epHandler(self.entry)
            ep_list = ep_class.pick_range()
            self.show_entries.append(
                {"show_entry": deepcopy(self.entry), "ep_list": deepcopy(ep_list)}
            )

    def process(self):
        for ent in self.show_entries:
            entry = ent["show_entry"]
            ep_list = ent["ep_list"]
            for i in ep_list:
                entry.ep = parsenum(i)
                entry.embed_url = ""
                ep_class = epHandler(entry)
                entry = ep_class.gen_eplink()
                url_class = videourl(entry, self.options.quality)
                url_class.stream_url()
                entry = url_class.get_entry()
                download(entry, self.options.quality, self.options.ffmpeg).download()

    def show(self):
        pass

    def post(self):
        pass
