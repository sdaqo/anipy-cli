from typing import TYPE_CHECKING
from anipy_cli.menus import SeasonalMenu
from anipy_cli.clis.base_cli import CliBase

if TYPE_CHECKING:
    from anipy_cli.arg_parser import CliArgs


class SeasonalCli(CliBase):
    def __init__(self, options: "CliArgs", rpc_client=None):
        super().__init__(options, rpc_client)

    def print_header(self):
        pass

    def take_input(self):
        pass

    def process(self):
        pass

    def show(self):
        pass

    def post(self):
        menu = SeasonalMenu(self.options, self.rpc_client)

        if self.options.auto_update:
            menu.download_latest()
        else:
            menu.run()