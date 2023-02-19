from anipy_cli.misc import error, dc_presence_connect
from anipy_cli.arg_parser import parse_args
from anipy_cli.config import Config
from anipy_cli.colors import cprint, colors
from anipy_cli.cli.clis import *


def run_cli() -> None:
    args = parse_args()

    rpc_client = None
    if Config().dc_presence:
        rpc_client = dc_presence_connect()

    if args.config:
        print(Config()._config_file)
        return
    elif args.delete:
        try:
            Config().history_file_path.unlink()
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
        args.auto_update: SeasonalCli,
    }

    cli_class = clis_dict.get(True, DefaultCli)

    cli_class(options=args, rpc_client=rpc_client).run()
