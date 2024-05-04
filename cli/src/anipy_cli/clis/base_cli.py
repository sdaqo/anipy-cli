from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from anipy_cli.arg_parser import CliArgs


class CliBase(ABC):
    def __init__(self, options: "CliArgs"):
        self.options = options

    @abstractmethod
    def print_header(self): ...

    @abstractmethod
    def take_input(self): ...

    @abstractmethod
    def process(self): ...

    @abstractmethod
    def show(self): ...

    @abstractmethod
    def post(self): ...

    def run(self):
        self.print_header()
        self.take_input()
        self.process()
        self.show()
        self.post()
