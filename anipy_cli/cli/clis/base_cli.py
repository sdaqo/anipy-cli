from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from anipy_cli.cli.arg_parser import CliArgs


class CliBase(ABC):
    def __init__(self, options: "CliArgs", rpc_client=None):
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
