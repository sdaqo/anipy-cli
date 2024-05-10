from typing import TYPE_CHECKING, Iterator, Optional, Type

from anipy_api.provider.providers import *
from anipy_api.provider.providers import __all__

if TYPE_CHECKING:
    from anipy_api.provider import BaseProvider


def list_providers() -> Iterator[Type["BaseProvider"]]:
    """List all available providers.

    Yields:
        Provider classes (that still need to be instantiated)

    Example:
        Here is how the cli uses this:
        ```python hl_lines="11-14"
        def get_prefered_providers(mode: str) -> Iterator["BaseProvider"]:
            config = Config()
            preferred_providers = config.providers[mode]

            if not preferred_providers:
                error(
                    f"you have no providers set for {mode} mode, look into your config",
                    fatal=True,
                )

            for i in list_providers():
                if i.NAME in preferred_providers:
                    url_override = config.provider_urls.get(i.NAME, None)
                    yield i(url_override)
        ```

    """
    for p in __all__:
        yield globals()[p]


def get_provider(
    name: str, base_url_override: Optional[str] = None
) -> Optional["BaseProvider"]:
    """Get a provider by name.

    Arguments:
        name: Name of the provider to get
        base_url_override: Override the url used by the provider.

    Returns:
        The provider by name, if it exsists
    """
    for p in list_providers():
        if p.NAME == name:
            return p(base_url_override)
