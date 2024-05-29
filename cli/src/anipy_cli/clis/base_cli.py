from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from anipy_cli.arg_parser import CliArgs


class CliBase(ABC):
    def __init__(self, options: "CliArgs"):
        self.options = options

    @abstractmethod
    def print_header(self) -> Optional[bool]: ...

    @abstractmethod
    def take_input(self) -> Optional[bool]: ...

    @abstractmethod
    def process(self) -> Optional[bool]: ...

    @abstractmethod
    def show(self) -> Optional[bool]: ...

    @abstractmethod
    def post(self) -> Optional[bool]: ...

    def run(self):
        funcs = ["print_header", "take_input", "process", "show", "post"]
        for f in funcs:
            func = getattr(self, f)
            ret = func()

            if ret == False:  # noqa: E712
                break
