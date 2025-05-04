from __future__ import annotations

import logging
import datetime
import os
from pathlib import Path

from anipy_cli.config import Config

from anipy_cli import __appname__
from appdirs import user_data_dir

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

logger = Logger(0)
