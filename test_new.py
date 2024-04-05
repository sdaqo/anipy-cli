from anipy_cli.provider.providers.gogo_provider import GoGoProvider
from anipy_cli.anime import Anime

provider = GoGoProvider()
search = provider.get_search("frieren")
# anime = Anime(provider, search[0])
print(provider.get_video(search[0].identifier, 27))
