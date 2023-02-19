from ...arg_parser import CliArgs
from ..menus import SeasonalMenu
from .base_cli import CliBase


class SeasonalCli(CliBase):
    def __init__(self, options: CliArgs, rpc_client=None):
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
