from typing import Optional

from pypresence.exceptions import DiscordNotFound

from anipy_cli.arg_parser import parse_args
from anipy_cli.clis import *
from anipy_cli.colors import colors, cprint
from anipy_cli.util import error
from anipy_cli.config import Config
from anipy_api.discord import dc_presence_connect


def run_cli(override_args: Optional[list[str]] = None):
    args = parse_args(override_args)
    config = Config()

    rpc_client = None
    if config.dc_presence:
        try:
            rpc_client = dc_presence_connect()
            cprint(colors.GREEN, "Initialized Discord Presence Client")
        except DiscordNotFound:
            rpc_client = None
            error("Discord is not opened, can't initialize Discord Presence")
        except ConnectionError:
            rpc_client = None
            error("Can't Connect to discord, can't initialize Discord Presence")

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
    elif args.refresh_config:
        config._create_config()
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
        cli_class(options=args, rpc_client=rpc_client).run()
    except KeyboardInterrupt:
        error("interrupted", fatal=True)


if __name__ == "__main__":
    run_cli()

