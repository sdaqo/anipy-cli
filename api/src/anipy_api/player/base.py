import os
import subprocess as sp
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Optional, Protocol

from anipy_api.error import PlayerError

if TYPE_CHECKING:
    from anipy_api.anime import Anime
    from anipy_api.provider import ProviderStream


class PlayCallback(Protocol):
    """Callback that gets called upon playing a title, it accepts a anime and the stream being played."""

    def __call__(self, anime: "Anime", stream: "ProviderStream"):
        """
        Args:
            anime: The anime argument passed to the callback. This is the currently playing anime.
            stream: The stream argument passed to the callback. That is the currently playing stream.
        """
        ...


class PlayerBase(ABC):
    """The abstract base class for all the players.

    To list available players or get one by name, use
    [list_players][anipy_api.player.player.list_players]
    and [get_player][anipy_api.player.player.get_player] respectively.
    """

    def __init__(self, play_callback: Optional[PlayCallback] = None):
        """__init__ of PlayerBase

        Args:
            play_callback: Callback called upon starting to play a title with `play_title`
        """
        self._play_callback = play_callback

    @abstractmethod
    def play_title(self, anime: "Anime", stream: "ProviderStream"):
        """Play a stream of an anime.

        Args:
            anime: The anime
            stream: The stream
        """
        ...

    @abstractmethod
    def play_file(self, path: str):
        """Play any file.

        Args:
            path: The path to the file
        """
        ...

    @abstractmethod
    def wait(self):
        """Wait for the player to stop/close."""
        ...

    @abstractmethod
    def kill_player(self):
        """Kill the player."""
        ...

    def _call_play_callback(self, anime: "Anime", stream: "ProviderStream"):
        if self._play_callback:
            self._play_callback(anime, stream)

    @staticmethod
    def _get_media_title(anime: "Anime", stream: "ProviderStream"):
        return f"[{anime.provider.NAME}] {anime.name} E{stream.episode} [{stream.language}][{stream.resolution}p]"


class SubProcessPlayerBase(PlayerBase):
    """The base class for all players that are run through a sub process.

    For documentation of the other functions look at the [base class][anipy_api.player.base.PlayerBase].

    Example:
        Here is how you might implement such a player on your own:
        ```python
        class Mpv(SubProcessPlayerBase):
            def __init__(self, player_path: str, extra_args: List[str] = [], rpc_client=None):
                self.player_args_template = [ # (1)
                    "{stream_url}",
                    "--force-media-title={media_title}",
                    "--force-window=immediate",
                    *extra_args,
                ]

                super().__init__(
                    rpc_client=rpc_client,
                    player_path=player_path,
                    extra_args=extra_args
                )
        ```

        1. This is the important part, those arguments will later be passed to the player.
        There are two format fields you can use `{stream_url}` and `{media_title}`.

    Attributes:
        player_args_template: A list of arguments that are passed to the player command.
            Fields that are replaced are `{media_title}` and `{stream_url}`.
            This is only important if you are implementing your own player.

    """

    player_args_template: List[str]

    @abstractmethod
    def __init__(
        self,
        player_path: str,
        extra_args: List[str],
        play_callback: Optional[PlayCallback] = None,
    ):
        """__init__ for SubProcessPlayerBase

        Args:
            player_path: The path to the player's executable
            extra_args: Extra arguments to be passed to the player
            play_callback: Callback called upon starting to play a title with `play_title`
        """
        super().__init__(play_callback)

        self._sub_proc = None
        self._player_exec = player_path

    def play_title(self, anime: "Anime", stream: "ProviderStream"):
        player_cmd = [
            i.format(
                media_title=self._get_media_title(anime, stream), stream_url=stream.url
            )
            for i in self.player_args_template
        ]
        player_cmd.insert(0, self._player_exec)

        if isinstance(self._sub_proc, sp.Popen):
            self.kill_player()

        self._sub_proc = self._open_sproc(player_cmd)
        self._call_play_callback(anime, stream)

    def play_file(self, path):
        if isinstance(self._sub_proc, sp.Popen):
            self.kill_player()

        player_cmd = [self._player_exec, path]
        self._sub_proc = self._open_sproc(player_cmd)

    def wait(self):
        if self._sub_proc is not None:
            self._sub_proc.wait()

    def kill_player(self):
        if self._sub_proc is not None:
            self._sub_proc.kill()

    @staticmethod
    def _open_sproc(player_command: List[str]) -> sp.Popen:
        try:
            if os.name in ("nt", "dos"):
                sub_proc = sp.Popen(player_command)
            else:
                sub_proc = sp.Popen(player_command, stdout=sp.PIPE, stderr=sp.DEVNULL)
        except FileNotFoundError:
            raise PlayerError(f"Executable {player_command[0]} was not found")

        return sub_proc
