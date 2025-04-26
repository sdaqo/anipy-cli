# Player/Provider Availabiltiy

This is page lists available/supported providers/players and their capabilities.

## Current Version

Version: 3.5.0

### Providers

| Identifier | URL                                            | Filter capabilties [^1]                    | Season Search [^2] | Notes                                                                                                                                                            | Reference                                                                           |
| ---------- | ---------------------------------------------- | ------------------------------------------ | ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| allanime   | [https://allmanga.to/](https://allmanga.to/)   | YEAR, SEASON, MEDIA_TYPE, NO_QUERY         | Yes                | [Hover Me]("Placeholder for future reference") **Recommended**                                                                                                   | [AllAnimeProvider][anipy_api.provider.providers.allanime_provider.AllAnimeProvider] |
| animekai   | [https://animekai.to/](https://animekai.to/)   | YEAR, SEASON, STATUS, MEDIA_TYPE, NO_QUERY | Yes                | [Hover Me]("Pretty unstable and may not work for extended periods of time, better use allanime")                                                                 | [AnimekaiProvider][anipy_api.provider.providers.animekai_provider.AnimekaiProvider] |

### Players

| Name             | Recognised Stem(s) [^3] | Project URL(s)                                                                                                           | Sub-process | Code Reference                                                          |
| ---------------- | ----------------------- | ------------------------------------------------------------------------------------------------------------------------ | ----------- | ----------------------------------------------------------------------- |
| mpv              | mpv, mpvnet             | [https://mpv.io/](https://mpv.io/), [https://github.com/mpvnet-player/mpv.net](https://github.com/mpvnet-player/mpv.net) | Yes         | [Mpv][anipy_api.player.players.mpv.Mpv]                                 |
| Syncplay         | syncplay                | [https://syncplay.pl/](https://syncplay.pl/])                                                                            | Yes         | [Syncplay][anipy_api.player.players.syncplay.Syncplay]                  |
| VLC Media Player | vlc                     | [https://www.videolan.org/vlc/](https://www.videolan.org/vlc/)                                                           | Yes         | [Vlc][anipy_api.player.players.vlc.Vlc]                                 |
| Mpv Controlled   | mpv-controlled          | [https://github.com/jaseg/python-mpv](https://github.com/jaseg/python-mpv)                                               | No          | [MpvControllable][anipy_api.player.players.mpv_control.MpvControllable] |
| IINA             | iina                    | [https://iina.io/](https://iina.io/)                                                                                     | Yes         | [Iina][anipy_api.player.players.iina.Iina]                              |

## Version 3.4.0

Version: 3.4.0

### Providers

| Identifier | URL                                            | Filter capabilties [^1]                    | Season Search [^2] | Notes                                                                                                                                                            | Reference                                                                           |
| ---------- | ---------------------------------------------- | ------------------------------------------ | ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| animekai   | [https://animekai.to/](https://animekai.to/)   | YEAR, SEASON, STATUS, MEDIA_TYPE, NO_QUERY | Yes                | [Hover Me]("Placeholder for future reference") **Recommended**                                                                                                   | [AnimekaiProvider][anipy_api.provider.providers.animekai_provider.AnimekaiProvider] |

### Players

| Name             | Recognised Stem(s) [^3] | Project URL(s)                                                                                                           | Sub-process | Code Reference                                                          |
| ---------------- | ----------------------- | ------------------------------------------------------------------------------------------------------------------------ | ----------- | ----------------------------------------------------------------------- |
| mpv              | mpv, mpvnet             | [https://mpv.io/](https://mpv.io/), [https://github.com/mpvnet-player/mpv.net](https://github.com/mpvnet-player/mpv.net) | Yes         | [Mpv][anipy_api.player.players.mpv.Mpv]                                 |
| Syncplay         | syncplay                | [https://syncplay.pl/](https://syncplay.pl/])                                                                            | Yes         | [Syncplay][anipy_api.player.players.syncplay.Syncplay]                  |
| VLC Media Player | vlc                     | [https://www.videolan.org/vlc/](https://www.videolan.org/vlc/)                                                           | Yes         | [Vlc][anipy_api.player.players.vlc.Vlc]                                 |
| Mpv Controlled   | mpv-controlled          | [https://github.com/jaseg/python-mpv](https://github.com/jaseg/python-mpv)                                               | No          | [MpvControllable][anipy_api.player.players.mpv_control.MpvControllable] |
| IINA             | iina                    | [https://iina.io/](https://iina.io/)                                                                                     | Yes         | [Iina][anipy_api.player.players.iina.Iina]                              |


## Version 3.3.0

Version: 3.3.0

### Providers

| Identifier | URL                                            | Filter capabilties [^1]                    | Season Search [^2] | Notes                                                                                                                                                            | Reference                                                                           |
| ---------- | ---------------------------------------------- | ------------------------------------------ | ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| gogoanime  | [https://gogoanime3.co](https://gogoanime3.co) | YEAR, SEASON, STATUS, NO_QUERY             | Yes                | [Hover Me]("As of now this provider does not update it's content, but is still online.")                                                                         | [GoGoProvider][anipy_api.provider.providers.gogo_provider.GoGoProvider]             |
| anivibe    | [https://anivibe.net/](https://anivibe.net/)   | YEAR, SEASON, STATUS, MEDIA_TYPE, NO_QUERY | Yes                | [Hover Me]("Placeholder for future reference")                                                                                                                   | [AnivibeProvider][anipy_api.provider.providers.anivibe_provider.AnivibeProvider]    |

### Players

| Name             | Recognised Stem(s) [^3] | Project URL(s)                                                                                                           | Sub-process | Code Reference                                                          |
| ---------------- | ----------------------- | ------------------------------------------------------------------------------------------------------------------------ | ----------- | ----------------------------------------------------------------------- |
| mpv              | mpv, mpvnet             | [https://mpv.io/](https://mpv.io/), [https://github.com/mpvnet-player/mpv.net](https://github.com/mpvnet-player/mpv.net) | Yes         | [Mpv][anipy_api.player.players.mpv.Mpv]                                 |
| Syncplay         | syncplay                | [https://syncplay.pl/](https://syncplay.pl/])                                                                            | Yes         | [Syncplay][anipy_api.player.players.syncplay.Syncplay]                  |
| VLC Media Player | vlc                     | [https://www.videolan.org/vlc/](https://www.videolan.org/vlc/)                                                           | Yes         | [Vlc][anipy_api.player.players.vlc.Vlc]                                 |
| Mpv Controlled   | mpv-controlled          | [https://github.com/jaseg/python-mpv](https://github.com/jaseg/python-mpv)                                               | No          | [MpvControllable][anipy_api.player.players.mpv_control.MpvControllable] |
| IINA             | iina                    | [https://iina.io/](https://iina.io/)                                                                                     | Yes         | [Iina][anipy_api.player.players.iina.Iina]                              |

## Version 3.2.0

Version: 3.2.0

### Providers

| Identifier | URL                                            | Filter capabilties [^1]                    | Season Search [^2] | Notes                                                                                                                                                            | Reference                                                                  |
| ---------- | ---------------------------------------------- | ------------------------------------------ | ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| gogoanime  | [https://gogoanime3.co](https://gogoanime3.co) | YEAR, SEASON, STATUS, NO_QUERY             | Yes                | [Hover Me]("If possible search for the japanese name instead of the english one, some entries in gogo do not have their alternative names configured properly.") | [GoGoProvider][anipy_api.provider.providers.gogo_provider.GoGoProvider]    |
| yugenanime | [https://yugenanime.tv](https://yugenanime.tv) | YEAR, SEASON, STATUS, MEDIA_TYPE, NO_QUERY | Yes                | [Hover Me]("Placeholder for future reference") **Recommended**                                                                                                   | [YugenProvider][anipy_api.provider.providers.yugen_provider.YugenProvider] |

### Players

| Name             | Recognised Stem(s) [^3] | Project URL(s)                                                                                                           | Sub-process | Code Reference                                                          |
| ---------------- | ----------------------- | ------------------------------------------------------------------------------------------------------------------------ | ----------- | ----------------------------------------------------------------------- |
| mpv              | mpv, mpvnet             | [https://mpv.io/](https://mpv.io/), [https://github.com/mpvnet-player/mpv.net](https://github.com/mpvnet-player/mpv.net) | Yes         | [Mpv][anipy_api.player.players.mpv.Mpv]                                 |
| Syncplay         | syncplay                | [https://syncplay.pl/](https://syncplay.pl/])                                                                            | Yes         | [Syncplay][anipy_api.player.players.syncplay.Syncplay]                  |
| VLC Media Player | vlc                     | [https://www.videolan.org/vlc/](https://www.videolan.org/vlc/)                                                           | Yes         | [Vlc][anipy_api.player.players.vlc.Vlc]                                 |
| Mpv Controlled   | mpv-controlled          | [https://github.com/jaseg/python-mpv](https://github.com/jaseg/python-mpv)                                               | No          | [MpvControllable][anipy_api.player.players.mpv_control.MpvControllable] |
| IINA             | iina                    | [https://iina.io/](https://iina.io/)                                                                                     | Yes         | [Iina][anipy_api.player.players.iina.Iina]                              |

## Version 3.0.0

Version: 3.0.0

### Providers

| Identifier | URL                                            | Filter capabilties [^1]        | Season Search [^2] | Notes                                                                                                                                                                            | Reference                                                               |
| ---------- | ---------------------------------------------- | ------------------------------ | ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| gogoanime  | [https://gogoanime3.co](https://gogoanime3.co) | YEAR, SEASON, STATUS, NO_QUERY | Yes                | [Hover Me]("If possible search for the japanese name instead of the english one, some entries in gogo do not have their alternative names configured properly.") **Recommended** | [GoGoProvider][anipy_api.provider.providers.gogo_provider.GoGoProvider] |

### Players

| Name             | Recognised Stem(s) [^3] | Project URL(s)                                                                                                           | Sub-process | Code Reference                                                          |
| ---------------- | ----------------------- | ------------------------------------------------------------------------------------------------------------------------ | ----------- | ----------------------------------------------------------------------- |
| mpv              | mpv, mpvnet             | [https://mpv.io/](https://mpv.io/), [https://github.com/mpvnet-player/mpv.net](https://github.com/mpvnet-player/mpv.net) | Yes         | [Mpv][anipy_api.player.players.mpv.Mpv]                                 |
| Syncplay         | syncplay                | [https://syncplay.pl/](https://syncplay.pl/])                                                                            | Yes         | [Syncplay][anipy_api.player.players.syncplay.Syncplay]                  |
| VLC Media Player | vlc                     | [https://www.videolan.org/vlc/](https://www.videolan.org/vlc/)                                                           | Yes         | [Vlc][anipy_api.player.players.vlc.Vlc]                                 |
| Mpv Controlled   | mpv-controlled          | [https://github.com/jaseg/python-mpv](https://github.com/jaseg/python-mpv)                                               | No          | [MpvControllable][anipy_api.player.players.mpv_control.MpvControllable] |

[^1]:
    Look here for infos about this
    [here](reference/anipy_api/provider/filter.md#anipy_api.provider.filter.FilterCapabilities),
    this is only important for API usage.

[^2]:
    This is a cli-specific capability, if a provider has the filter
    capabilities YEAR, SEASON and NO_QUERY it is eligible for this.

[^3]:
    The Stem is the end part of a path without it's suffix e.g. the stem of
    `mpv.exe` is `mpv`.
