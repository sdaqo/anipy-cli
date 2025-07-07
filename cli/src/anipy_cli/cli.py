from pathlib import Path
from types import TracebackType
from typing import Optional

from pypresence.exceptions import DiscordNotFound

from anipy_api.locallist import LocalList
from anipy_cli.prompts import migrate_provider

from anipy_cli.arg_parser import CliArgs, parse_args
from anipy_cli.clis import *
from anipy_cli.colors import color, colors, cprint
from anipy_cli.util import error, DotSpinner, migrate_locallist
from anipy_cli.config import Config
from anipy_cli.discord import DiscordPresence
import anipy_cli.logger as logger


def run_cli(override_args: Optional[list[str]] = None):
    args = parse_args(override_args)

    logger.set_cli_verbosity(args.verbosity)
    logger.set_stack_always(args.stack_always)

    def fatal_handler(exc_val: BaseException, exc_tb: TracebackType, logs_location: Path):
        print(
            color(
                colors.RED,
                f'A fatal error of type [{exc_val.__class__.__name__}] has occurred with message "{exc_val.args[0]}". Logs can be found at {logs_location}.',
            )
        )

    with logger.safe(fatal_handler):
        _safe_cli(args)


def _safe_cli(args: CliArgs):
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
    elif args.migrate_hist:
        history_list = LocalList(
            Config()._history_file_path, migrate_cb=migrate_locallist
        )
        migrate_provider("default", history_list)
        return

    clis_dict = {
        args.download: DownloadCli,
        args.binge: BingeCli,
        args.seasonal: SeasonalCli,
        args.history: HistoryCli,
        args.mal: MalCli,
        args.anilist: AniListCli,
    }

    cli_class = clis_dict.get(True, DefaultCli)

    try:
        cli_class(options=args).run()
    except KeyboardInterrupt:
        error("interrupted", fatal=True)


if __name__ == "__main__":
    run_cli()
