from typing import TYPE_CHECKING, Iterator, Type
from anipy_api.provider.providers.gogo_provider import GoGoProvider

if TYPE_CHECKING:
    from anipy_api.provider import BaseProvider

__all__ = ["GoGoProvider"]


def list_providers() -> Iterator[Type["BaseProvider"]]:
    for p in __all__:
        yield globals()[p]
