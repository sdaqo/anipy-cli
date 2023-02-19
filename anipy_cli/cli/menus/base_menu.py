import sys

from ...misc import error, clear_console
from ...colors import colors, color

from dataclasses import dataclass
from typing import Callable
from abc import ABC, abstractmethod


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
    def menu_options(self) -> list[MenuOption]:
        pass

    @abstractmethod
    def print_header(self):
        pass

    def run(self):
        self.print_options()
        self.take_input()

    def take_input(self):
        while True:
            picked = input("Enter option: ")
            op = next(
                filter(
                    lambda x: x.trigger == picked, self.menu_options
                ), None
            )

            if op is None:
                error("invalid input")

            op.callback()

    def print_options(self, clear_screen=True):
        if clear_screen:
            clear_console()
        self.print_header()
        for op in self.menu_options:
            print(op)

    def quit(self):
        sys.exit()


