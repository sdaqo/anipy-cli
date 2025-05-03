from __future__ import annotations

import logging

class Logger:
    """
    A class that logs information to
    a file, and can be configured to 
    log to the console as well.
    """
    LOGGER_NAME = "cli_logger"

    def __init__(self, file_log_level: logging._Level, console_log_level: logging._Level = 60) -> None:
        self._logger = logging.getLogger(self.LOGGER_NAME)

        self.file_log_level = file_log_level
        self.console_log_level = console_log_level

    def _init_logger(self, logger: logging.Logger):
        logger.setLevel(logging.DEBUG)

        file_formatter = logging.Formatter("{asctime} - {levelname} - {message}", style="{", datefmt="%Y-%m-%d %H:%M:%S:%f")
        console_formatter = logging.Formatter("{levelname} -> {message}", style="{")

        self.console_handler = logging.StreamHandler()
        self.console_handler.setFormatter(console_formatter)
        logger.addHandler(self.console_handler)

        self.file_handler = logging.FileHandler("")
        self.file_handler.setFormatter(file_formatter)
        logger.addHandler(self.file_handler)
    
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
        self.console_handler 

    def debug(self, content: str, exc_info: logging._ExcInfoType = None, stack_info: bool = False):
        self._logger.debug(content, exc_info=exc_info, stack_info=stack_info)

    def info(self, content: str, exc_info: logging._ExcInfoType = None, stack_info: bool = False):
        self._logger.info(content, exc_info=exc_info, stack_info=stack_info)

    def warn(self, content: str, exc_info: logging._ExcInfoType = None, stack_info: bool = False):
        self._logger.warning(content, exc_info=exc_info, stack_info=stack_info)

    def error(self, content: str, exc_info: logging._ExcInfoType = None, stack_info: bool = False):
        self._logger.error(content, exc_info=exc_info, stack_info=stack_info)

    def fatal(self, content: str, exc_info: logging._ExcInfoType = None, stack_info: bool = False):
        self._logger.critical(content, exc_info=exc_info, stack_info=stack_info)

logger = Logger(logging.WARN)
