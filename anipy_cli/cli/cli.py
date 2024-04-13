from typing import Optional
from pypresence.exceptions import DiscordNotFound

from anipy_cli.discord import dc_presence_connect
from anipy_cli.cli.arg_parser import parse_args
from anipy_cli.config import Config
from anipy_cli.cli.util import error
from anipy_cli.cli.colors import cprint, colors
from anipy_cli.cli.clis import *


def run_cli(override_args: Optional[list[str]] = None):
    args = parse_args(override_args)

    rpc_client = None
    if Config().dc_presence:
        try:
            rpc_client = dc_presence_connect()
            # cprint(colors.GREEN, "Initialized Discord Presence Client")
        except DiscordNotFound:
            rpc_client = None
            # cprint(colors.RED, "Discord is not opened, can't initialize Discord Presence")
        except ConnectionError:
            rpc_client = None
            # cprint(colors.RED, "Can't Connect to discord.")

    if args.config:
        print(Config()._config_file)
        return
    elif args.delete:
        try:
            Config()._history_file_path.unlink()
            cprint(colors.RED, "Done")
        except FileNotFoundError:
            error("no history file found")
        return
    elif args.refresh_config:
        Config()._create_config()
        return

    clis_dict = {
        args.download: DownloadCli,
        args.binge: BingeCli,
        args.seasonal: SeasonalCli,
        args.history: HistoryCli,
        args.mal: MalCli,
        args.auto_update: SeasonalCli,
    }

    cli_class = clis_dict.get(True, DefaultCli)
    
    try:
        cli_class(options=args, rpc_client=rpc_client).run()
    except KeyboardInterrupt:
        error("interrupted", fatal=True)
