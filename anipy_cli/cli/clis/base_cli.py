import sys
from abc import ABC, abstractmethod

from anipy_cli.arg_parser import CliArgs
from anipy_cli.misc import error


class CliBase(ABC):
    def __init__(self, options: CliArgs, rpc_client=None):
        self.options = options
        self.rpc_client = rpc_client

    @abstractmethod
    def print_header(self):
        pass

    @abstractmethod
    def take_input(self):
        pass

    @abstractmethod
    def process(self):
        pass

    @abstractmethod
    def show(self):
        pass

    @abstractmethod
    def post(self):
        pass

    def run(self):
        self.print_header()
        self.take_input()
        self.process()
        self.show()
        self.post()

    @staticmethod
    def exit(error_str: str):
        error(error_str)
        sys.exit()
