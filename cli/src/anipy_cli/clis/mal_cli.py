from typing import TYPE_CHECKING

from anipy_api.error import MyAnimeListError
from anipy_api.mal import MyAnimeList
from InquirerPy import inquirer

from anipy_cli.clis.base_cli import CliBase
from anipy_cli.config import Config
from anipy_cli.menus import MALMenu
from anipy_cli.util import DotSpinner, error

if TYPE_CHECKING:
    from anipy_cli.arg_parser import CliArgs


class MalCli(CliBase):
    def __init__(self, options: "CliArgs"):
        super().__init__(options)
        self.user = ""
        self.password = ""
        self.mal = None

    def print_header(self):
        pass

    def take_input(self):
        config = Config()
        self.user = config.mal_user
        self.password = self.options.mal_password or config.mal_password

        if not self.user:
            self.user = inquirer.text(  # type: ignore
                "Your MyAnimeList Username:",
                validate=lambda x: len(x) > 1,
                invalid_message="You must enter a username!",
                long_instruction="Hint: You can save your username and password in the config!",
            ).execute()

        if not self.password:
            self.password = inquirer.secret(  # type: ignore
                "Your MyAnimeList Password:",
                transformer=lambda _: "[hidden]",
                validate=lambda x: len(x) > 1,
                invalid_message="You must enter a password!",
                long_instruction="Hint: You can also pass the password via the `--mal-password` option!",
            ).execute()

    def process(self):
        try:
            with DotSpinner("Logging into MyAnimeList..."):
                self.mal = MyAnimeList.from_password_grant(self.user, self.password)
        except MyAnimeListError as e:
            error(
                f"{str(e)}\nCannot login to MyAnimeList, it is likely your credentials are wrong",
                fatal=True,
            )

    def show(self):
        pass

    def post(self):
        assert self.mal is not None

        menu = MALMenu(mal=self.mal, options=self.options)

        if self.options.auto_update:
            menu.download()
        elif self.options.mal_sync_seasonals:
            menu.sync_mal_seasonls()
        else:
            menu.run()
