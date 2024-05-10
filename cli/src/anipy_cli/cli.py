from typing import Optional

from pypresence.exceptions import DiscordNotFound

from anipy_cli.arg_parser import parse_args
from anipy_cli.clis import *
from anipy_cli.colors import colors, cprint
from anipy_cli.util import error, DotSpinner
from anipy_cli.config import Config
from anipy_cli.discord import DiscordPresence


def run_cli(override_args: Optional[list[str]] = None):
    args = parse_args(override_args)
    config = Config()
    # This updates the config, adding new values doc changes and the like.
    config._create_config()

    if config.dc_presence:
        with DotSpinner("Intializing Discord Presence...") as s:
            try:
                DiscordPresence()
                s.set_text(colors.GREEN, "Initialized Discord Presence")
                s.ok("✔")
            except DiscordNotFound:
                s.set_text(
                    colors.RED,
                    "Discord is not opened, can't initialize Discord Presence",
                )
                s.fail("✘")
            except ConnectionError:
                s.set_text(
                    colors.RED,
                    "Can't Connect to discord, can't initialize Discord Presence",
                )
                s.fail("✘")

    if args.config:
        print(config._config_file)
        return
    elif args.delete:
        try:
            config._history_file_path.unlink()
            cprint(colors.RED, "Done")
        except FileNotFoundError:
            error("no history file found")
        return

    clis_dict = {
        args.download: DownloadCli,
        args.binge: BingeCli,
        args.seasonal: SeasonalCli,
        args.history: HistoryCli,
        args.mal: MalCli,
    }

    cli_class = clis_dict.get(True, DefaultCli)

    try:
        cli_class(options=args).run()
    except KeyboardInterrupt:
        error("interrupted", fatal=True)


if __name__ == "__main__":
    run_cli()
