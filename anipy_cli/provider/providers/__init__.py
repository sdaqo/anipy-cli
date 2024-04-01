from typing import Iterator
from anipy_cli.provider import BaseProvider
from anipy_cli.provider.providers.gogo_provider import GoGoProvider

__all__ = ["GoGoProvider"]


def list_providers() -> Iterator[BaseProvider]:
    for p in __all__:
        yield globals()[p]
