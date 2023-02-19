from anipy_cli.arg_parser import CliArgs
from anipy_cli.misc import Entry, error, print_names
from anipy_cli.colors import cinput, colors
from anipy_cli.history import history
from anipy_cli.url_handler import epHandler, videourl
from anipy_cli.player import get_player
from anipy_cli.cli.menus import Menu
from anipy_cli.cli.clis.base_cli import CliBase


class HistoryCli(CliBase):
    def __init__(self, options: CliArgs, rpc_client=None):
        super().__init__(options, rpc_client)

        self.entry = Entry()
        self.player = get_player(
            rpc_client=self.rpc_client, player_override=self.options.optional_player
        )
        self.hist = history(self.entry).read_save_data()

    def print_header(self):
        pass

    def take_input(self):
        if not self.hist:
            self.exit("No History")

        shows = [x for x in self.hist]
        print_names(shows)

        while True:
            inp = cinput(colors.CYAN, "Enter Number: ")
            try:
                if int(inp) <= 0:
                    raise ValueError

                picked = shows[int(inp) - 1]
                break
            except ValueError:
                error("invalid input")
            except IndexError:
                error("invalid Input")

        self.entry.show_name = picked
        self.entry.ep = self.hist[picked]["ep"]
        self.entry.ep_url = self.hist[picked]["ep-link"]
        self.entry.category_url = self.hist[picked]["category-link"]
        self.entry.latest_ep = epHandler(self.entry).get_latest()

    def process(self):
        url_parser = videourl(self.entry, self.options.quality)
        url_parser.stream_url()
        self.entry = url_parser.get_entry()

    def show(self):
        self.player.play_title(self.entry)

    def post(self):
        Menu(
            options=self.options,
            entry=self.entry,
            player=self.player,
            rpc_client=self.rpc_client,
        ).run()
