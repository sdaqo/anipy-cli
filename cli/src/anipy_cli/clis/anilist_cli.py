from typing import TYPE_CHECKING

from anipy_api.error import AniListError
from anipy_api.anilist import AniList
from InquirerPy import inquirer

from anipy_cli.clis.base_cli import CliBase
from anipy_cli.config import Config
from anipy_cli.menus import AniListMenu
from anipy_cli.util import DotSpinner, error
import webbrowser

if TYPE_CHECKING:
    from anipy_cli.arg_parser import CliArgs


class AniListCli(CliBase):
    def __init__(self, options: "CliArgs"):
        super().__init__(options)
        self.access_token = ""
        self.anilist = None

    def print_header(self):
        pass

    def take_input(self):
        config = Config()
        self.access_token = config.anilist_token

        if not self.access_token:
            webbrowser.open(AniList.AUTH_URL)
            self.access_token = inquirer.text(  # type: ignore
                "Paste the token from the browser for Auth",
                validate=lambda x: len(x) > 1,
                invalid_message="You must enter a access_token!",
                long_instruction="Hint: You can save your access token in the config!",
            ).execute()

    def process(self):
        try:
            with DotSpinner("Logging into AniList..."):
                self.anilist = AniList.from_implicit_grant(self.access_token)
        except AniListError as e:
            error(
                f"{str(e)}\nCannot login to AniList, it is likely your response token is wrong",
                fatal=True,
            )

    def show(self):
        pass

    def post(self):
        assert self.anilist is not None

        menu = AniListMenu(anilist=self.anilist, options=self.options)

        if self.options.auto_update:
            menu.download()
        elif self.options.anilist_sync_seasonals:
            menu.sync_anilist_seasonls()
        else:
            menu.run()
