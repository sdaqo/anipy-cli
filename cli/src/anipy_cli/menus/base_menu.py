import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, List

from anipy_cli.colors import color, colors
from anipy_cli.util import error


@dataclass(frozen=True)
class MenuOption:
    info: str
    callback: Callable
    trigger: str

    def __repr__(self):
        return color(colors.GREEN, f"[{self.trigger}] ") + self.info


class MenuBase(ABC):
    @property
    @abstractmethod
    def menu_options(self) -> List[MenuOption]: ...

    @abstractmethod
    def print_header(self): ...

    def run(self):
        self.print_options()
        self.take_input()

    def take_input(self):
        while True:
            picked = input("Enter option: ")
            op = next(filter(lambda x: x.trigger == picked, self.menu_options), None)

            if op is None:
                error("invalid input")
                continue

            op.callback()

    def print_options(self, clear_screen=True):
        if clear_screen:
            os.system("cls" if os.name == "nt" else "clear")

        self.print_header()
        for op in self.menu_options:
            print(op)
