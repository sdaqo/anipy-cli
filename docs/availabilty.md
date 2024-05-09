# Player/Provider Availabiltiy

This is page lists available/supported providers/players and their capabilities.

## Current Version

Version: 3.0.0

### Providers

| Name      | Identifier | URL                                            | Filter capabilties [^1]        | Season Search [^2] | Code Reference                                                                                                                 |
| --------- | ---------- | ---------------------------------------------- | ------------------------------ | ------------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| GoGoAnime | gogoanime  | [https://gogoanime3.co](https://gogoanime3.co) | YEAR, SEASON, STATUS, NO_QUERY | Yes                | [GoGoProvider](reference/anipy_api/provider/providers/gogo_provider.md#anipy_api.provider.providers.gogo_provider.GoGoProvider) |

### Players

| Name             | Recognised Stem(s) [^3] | Project URL(s)                                                                                                           | Sub-process | Code Reference                                                                                                           |
| ---------------- | ----------------------- | ------------------------------------------------------------------------------------------------------------------------ | ----------- | ------------------------------------------------------------------------------------------------------------------------ |
| mpv              | mpv, mpvnet             | [https://mpv.io/](https://mpv.io/), [https://github.com/mpvnet-player/mpv.net](https://github.com/mpvnet-player/mpv.net) | Yes         | [Mpv](reference/anipy_api/player/players/mpv.md#anipy_api.player.players.mpv.Mpv)                                         |
| Syncplay         | syncplay                | [https://syncplay.pl/](https://syncplay.pl/])                                                                            | Yes         | [Syncplay](reference/anipy_api/player/players/syncplay.md#anipy_api.player.players.syncplay.Syncplay)                     |
| VLC Media Player | vlc                     | [https://www.videolan.org/vlc/](https://www.videolan.org/vlc/)                                                           | Yes         | [Vlc](reference/anipy_api/player/players/vlc.md#anipy_api.player.players.vlc.Vlc)                                         |
| Mpv Controlled   | mpv-controlled          | [https://github.com/jaseg/python-mpv](https://github.com/jaseg/python-mpv)                                               | No          | [MpvControllable](reference/anipy_api/player/players/mpv_control.md#anipy_api.player.players.mpv_control.MpvControllable) |

[^1]:
    Look here for infos about this
    [here](reference/anipy_api/provider/filter.md#anipy_api.provider.filter.FilterCapabilities),
    this is only important for API usage.

[^2]:
    This is a cli-specific capability, if a provider has the filter
    capabilities YEAR, SEASON and NO_QUERY it is eligible for this.

[^3]:
    The Stem is the end part of a path without it's suffix e.g. the stem of
    `/usr/bin/mpv.exe` <sub>(wow this is cursed)</sub> is `mpv`.
