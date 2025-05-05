from __future__ import annotations

import logging
import datetime
import os
from pathlib import Path
import sys
from types import TracebackType
from typing import Protocol

from anipy_cli.config import Config

from anipy_cli import __appname__
from appdirs import user_data_dir

class FatalHandler(Protocol):
    def __call__(self, exc_val: BaseException, exc_tb: TracebackType, logs_location: Path):
        ...

class FatalCatcher:
    def __init__(self, logger: Logger, logs_location: Path, fatal_handler: FatalHandler | None = None, ignore_system_exit: bool = True):
        self._logger = logger
        self._fatal_handler = fatal_handler

        self.logs_location = logs_location
        self.ignore_system_exit = ignore_system_exit

    def __enter__(self):
        self._logger.info("Initializing program...")
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None):
        if (not exc_type) or (not exc_val) or (not exc_tb):
            self._logger.info("Program exited successfully...")
            return True

        if (exc_type == SystemExit and self.ignore_system_exit):
            return True

        try:
            # Attempt to let a handler know something is up
            # so it can get to the user
            if self._fatal_handler:
                self._fatal_handler(exc_val, exc_tb, self.logs_location)
        except Exception:
            # If that fails, at least get something to the user
            sys.stderr.write("An extra fatal error occurred...")

        self._logger.fatal(f"A fatal error has occurred - {",".join(str(exc_val.args))}", exc_val)
        self._logger.info("Program exited with fatal errors...")

        return True # Return true because we have processed the error

class Logger:
    """
    A class that logs information to
    a file, and can be configured to 
    log to the console as well.
    """
    LOGGER_NAME = "cli_logger"
    MAX_LOGS = 5

    def __init__(self, file_log_level: logging._Level, console_log_level: logging._Level = 60) -> None:
        self._logger = logging.getLogger(self.LOGGER_NAME)

        self._init_logger(self._logger)

        self.file_log_level = file_log_level
        self.console_log_level = console_log_level

    def _init_logger(self, logger: logging.Logger):
        logger.setLevel(0)

        file_formatter = logging.Formatter("{asctime} - {levelname} - {message}", style="{", datefmt=r"%Y-%m-%d %H:%M:%S")
        console_formatter = logging.Formatter("{levelname} -> {message}", style="{")

        self.console_handler = logging.StreamHandler()
        self.console_handler.setFormatter(console_formatter)
        logger.addHandler(self.console_handler)

        self._clean_logs()
        current_time = datetime.datetime.now()
        self.file_handler = logging.FileHandler(self.logs_location / f"{current_time.isoformat().replace(':', '.')}.log", mode="a", encoding="utf-8")
        self.file_handler.setFormatter(file_formatter)
        logger.addHandler(self.file_handler)
    
    def _clean_logs(self):
        log_dir = self.logs_location
        if not os.path.exists(log_dir): 
            os.mkdir(log_dir)
        
        alllogs = os.listdir(log_dir)
        allsorted = sorted(alllogs, key = lambda log: os.path.getmtime(log_dir / log))

        if (len(allsorted) < self.MAX_LOGS):
            return allsorted
        
        os.remove(log_dir / allsorted[0]) # Delete
        allsorted.pop(0) # Remove from list
        return allsorted
    
    @property
    def file_log_level(self):
        return self._file_log_level
    
    @file_log_level.setter
    def file_log_level(self, value: logging._Level):
        self._file_log_level = value
        self.file_handler.setLevel(value)

    @property
    def console_log_level(self):
        return self._console_log_level
    
    @console_log_level.setter
    def console_log_level(self, value: logging._Level):
        self._console_log_level = value
        self.console_handler.setLevel(value)

    @property
    def logs_location(self):
        user_file_path = Path()
        try:
            user_file_path = Config().user_files_path
        except Exception:
            user_file_path = Path(user_data_dir(__appname__, appauthor=False))
        finally:
            return user_file_path / "logs"
    
    def setCliVerbosity(self, level: int):
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
        other = 10 # If anything else, default to debug.
        self.console_handler.setLevel(level_conversion.get(level, other))
    
    def safe(self, fatal_handler: FatalHandler|None = None):
        return FatalCatcher(self, self.logs_location, fatal_handler)

    def debug(self, content: str, exc_info: logging._ExcInfoType = None, stack_info: bool = False):
        self._logger.debug(content, exc_info=exc_info, stack_info=stack_info)

    def info(self, content: str, exc_info: logging._ExcInfoType = None, stack_info: bool = False):
        self._logger.info(content, exc_info=exc_info, stack_info=stack_info)

    def warn(self, content: str, exc_info: logging._ExcInfoType = None, stack_info: bool = False):
        self._logger.warning(content, exc_info=exc_info, stack_info=stack_info)

    def error(self, content: str, exc_info: logging._ExcInfoType = None):
        self._logger.error(content, exc_info=exc_info, stack_info=True)

    def fatal(self, content: str, exc_info: logging._ExcInfoType = None):
        self._logger.critical(content, exc_info=exc_info, stack_info=True)
    
    def log(self, level: int, content: str, exc_info: logging._ExcInfoType = None):
        self._logger.log(level, content, exc_info=exc_info)

logger = Logger(0)
