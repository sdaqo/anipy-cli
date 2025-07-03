from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path
import sys
from types import TracebackType
from typing import Protocol
import datetime

from anipy_cli.config import Config
from anipy_cli import __appname__
from appdirs import user_data_dir


class FatalHandler(Protocol):
    def __call__(
        self, exc_val: BaseException, exc_tb: TracebackType, logs_location: Path
    ): ...


class FatalCatcher:
    def __init__(
        self,
        logs_location: Path,
        fatal_handler: FatalHandler | None = None,
        ignore_system_exit: bool = True,
    ):
        self._fatal_handler = fatal_handler

        self.logs_location = logs_location
        self.ignore_system_exit = ignore_system_exit

    def __enter__(self):
        info("Initializing program...")
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ):
        if (not exc_type) or (not exc_val) or (not exc_tb):
            info("Program exited successfully...")
            return True

        if exc_type is SystemExit and self.ignore_system_exit:
            return True

        try:
            # Attempt to let a handler know something is up
            # so it can get to the user
            if self._fatal_handler:
                self._fatal_handler(exc_val, exc_tb, self.logs_location)
        except Exception:
            # If that fails, at least get something to the user
            sys.stderr.write("An extra fatal error occurred...")

        fatal(f"A fatal error has occurred - {','.join(exc_val.args)}", exc_val)
        info("Program exited with fatal errors...")

        return True  # Return true because we have processed the error


LOGGER_NAME = "cli_logger"
MAX_LOGS = 5
DEFAULT_FILE_LOG_LEVEL = 10
DEFAULT_CONSOLE_LOG_LEVEL = 60


def get_logs_location():
    user_file_path = Path()
    try:
        user_file_path = Config().user_files_path
    except Exception:
        user_file_path = Path(user_data_dir(__appname__, appauthor=False))
    finally:
        return user_file_path / "logs"

_logger = logging.getLogger(LOGGER_NAME)

_logger.setLevel(10)

file_formatter = logging.Formatter(
    "{asctime} - {levelname} - {message}", style="{", datefmt=r"%Y-%m-%d %H:%M:%S"
)
console_formatter = logging.Formatter("{levelname} -> {message}", style="{")

console_handler = logging.StreamHandler()
console_handler.setFormatter(console_formatter)
console_handler.setLevel(DEFAULT_CONSOLE_LOG_LEVEL)
_logger.addHandler(console_handler)

log_dir = get_logs_location()
log_dir.mkdir(parents=True, exist_ok=True)

current_time = datetime.datetime.now()
file_handler = logging.handlers.RotatingFileHandler(
    get_logs_location() / f"{current_time.isoformat().replace(':', '.')}.log",
    backupCount=5,
    encoding="utf-8",
)
file_handler.setFormatter(file_formatter)
file_handler.setLevel(DEFAULT_FILE_LOG_LEVEL)
_logger.addHandler(file_handler)


def get_console_log_level():
    return console_handler.level


def set_console_log_level(value: logging._Level):
    console_handler.setLevel(value)


def get_file_log_level():
    return file_handler.level


def set_file_log_level(value: logging._Level):
    file_handler.setLevel(value)


def set_cli_verbosity(level: int):
    """
    Set how extreme the error has to
    be for it to be printed in the CLI.

    Default is 0.

    0 = No Statements To CLI
    1 = Fatal
    2 = Warnings
    3 = Info
    """
    level_conversion = {
        0: 60,
        1: 50,
        2: 30,
        3: 20,
    }
    other = 10  # If anything else, default to debug.
    console_handler.setLevel(level_conversion.get(level, other))


def safe(fatal_handler: FatalHandler | None = None):
    return FatalCatcher(get_logs_location(), fatal_handler)


_stack_always = False


def set_stack_always(value: bool):
    global _stack_always

    _stack_always = value


def is_stack_always(passthrough: bool):
    """
    If _stack_always is true, return true.

    Otherwise return passthrough.
    """
    return True if _stack_always else passthrough


def debug(
    content: str, exc_info: logging._ExcInfoType = None, stack_info: bool = False
):
    _logger.debug(content, exc_info=exc_info, stack_info=is_stack_always(stack_info))


def info(content: str, exc_info: logging._ExcInfoType = None, stack_info: bool = False):
    _logger.info(content, exc_info=exc_info, stack_info=is_stack_always(stack_info))


def warn(content: str, exc_info: logging._ExcInfoType = None, stack_info: bool = False):
    _logger.warning(content, exc_info=exc_info, stack_info=is_stack_always(stack_info))


def error(content: str, exc_info: logging._ExcInfoType = None):
    _logger.error(content, exc_info=exc_info, stack_info=True)


def fatal(content: str, exc_info: logging._ExcInfoType = None):
    _logger.critical(content, exc_info=exc_info, stack_info=True)


def log(
    level: int,
    content: str,
    exc_info: logging._ExcInfoType = None,
    stack_info: bool = False,
):
    _logger.log(
        level, content, exc_info=exc_info, stack_info=is_stack_always(stack_info)
    )
