from typing import TYPE_CHECKING, Iterator, Type
from anipy_cli.provider.providers.gogo_provider import GoGoProvider

if TYPE_CHECKING:
    from anipy_cli.provider import BaseProvider

__all__ = ["GoGoProvider"]


def list_providers() -> Iterator[Type["BaseProvider"]]:
    for p in __all__:
        yield globals()[p]
