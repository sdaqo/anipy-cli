from anipy_cli.arg_parser import CliArgs
from anipy_cli.cli.menus import MALMenu
from anipy_cli.cli.clis.base_cli import CliBase


class MalCli(CliBase):
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
        menu = MALMenu(options=self.options, rpc_client=self.rpc_client)
        if self.options.auto_update:
            menu.download(mode="all")
        else:
            menu.run()
