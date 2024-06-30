## What is a provider?
A provider in anipy-api is the building stone that connects us to the anime we want! A provder may be a external anime site or even your local files (this is planned, Coming Soon!). Every provider bases on the [BaseProvider][anipy_api.provider.base.BaseProvider] and has the same basic functions: `get_search`, `get_episodes`, `get_info` and `get_video`.

You can check which providers anipy-cli supports [here](../../availabilty.md) or [here][anipy_api.provider.provider] (in the `providers` drop-down).

## Getting a provider instance
To get a provider you can use the [list_providers][anipy_api.provider.provider.list_providers] function, [get_provider][anipy_api.provider.provider.get_provider] to get a provider by its string representation or just simply import it directly.

```python
from anipy_api.provider import list_providers, get_provider 


# List providers
for p in list_providers():
    if p.NAME == "gogoanime":
        # You have to instantiate the provider to use it.
        provider = provider()

# If you know the name of the provider you could also do:
provider = get_provider("gogoanime", base_url_overrride="https://test.com") #(1)

# You can also import
from anipy_api.provider.providers import GoGoProvider
provider = GoGoProvider()

print(provider.NAME) # -> gogoanime
print(provider.BASE_URL) # -> https://test.com
```

1.  Furthermore, you can specify a url override for each provider!

## Searching
Searching can be done with the [get_search][anipy_api.provider.BaseProvider.get_search] method, you can even filter!
```python
results = provider.get_search("frieren") # (1)
```

1. Just FYI, we are using the same provider we got in the above example!

This returns a list of [ProviderSearchResult][anipy_api.provider.base.ProviderSearchResult] objects. Each contains the identifier of the anime, the name and a set of language types the anime supports. The language type set tells you if the anime supports dub/sub format.

#### Filtering
Every provider has a `FILTER_CAPS` attribute, it specifies which filters the provider supports.
```python
from anipy_api.provider import Filters, FilterCapabilities, Season

if provider.FILTER_CAPS & ( # (1)
    FilterCapabilities.SEASON
    | FilterCapabilities.YEAR
    | FilterCapabilities.NO_QUERY # (2)
):
    filters = Filters( # (3)
        year=2023,
        season=Season.FALL,
    )
    fall_2023_anime = provider.get_search("", filters=filters) # (4)
```

1. You can use bitwise operators here because this is a Flag class, check out the offical [documentation](https://docs.python.org/3/library/enum.html#enum.Flag), you may also use the `in` keyword.
2. If a provider supports NO_QUERY it means that if you search without query you get all available anime in its database.
3. If you use filters not supported by the provider, they will get skipped, no error will be raised.
4. Here we search without query, because we want to get all the anime available that are in the fall season of 2023.

## Putting it all together
```python
from anipy_api.provider import get_provider 

provider = get_provider("gogoanime")
frieren = provider.get_search("frieren")[0]

if provider.FILTER_CAPS & (
    FilterCapabilities.SEASON
    | FilterCapabilities.YEAR
    | FilterCapabilities.NO_QUERY
):
    filters = Filters(
        year=2023,
        season=Season.FALL,
    )
    fall_2023_anime = provider.get_search("", filters=filters)

    if frieren in fall_2023_anime:
        print("Frieren is an fall 2023 anime!") 
```

## Thats about it here
But... `get_episodes`, `get_info` and `get_video` were not covered!

Those are covered in the second example page [2. Anime](anime.md). The next page describes a wrapper for the search results that represents an anime, you can still use the functions directly from the provider but you would probably use them in the Anime class, but feel free to do it how you want!
