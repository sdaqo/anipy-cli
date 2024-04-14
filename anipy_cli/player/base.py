import os
import subprocess as sp
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List

from anipy_cli.discord import dc_presence
from anipy_cli.error import PlayerError
from anipy_cli.history import update_history

if TYPE_CHECKING:
    from anipy_cli.anime import Anime
    from anipy_cli.provider import ProviderStream


class PlayerBase(ABC):
    @property
    @abstractmethod
    def rpc_client(self): ...

    @abstractmethod
    def play_title(self, anime: "Anime", stream: "ProviderStream"): ...

    @abstractmethod
    def play_file(self, path: str): ...

    @abstractmethod
    def wait(self): ...

    @abstractmethod
    def kill_player(self): ...

    def _start_dc_presence(self, anime: "Anime", stream: "ProviderStream"):
        if self.rpc_client:
            dc_media_title = (
                f"{anime.name} | {stream.episode}/{anime.get_episodes(stream.dub)[-1]}"
            )
            dc_presence(dc_media_title, anime.get_info(), self.rpc_client)

    @staticmethod
    def _write_hist(anime: "Anime", stream: "ProviderStream"):
        update_history(anime, stream.episode, stream.dub)

    @staticmethod
    def _get_media_title(anime: "Anime", stream: "ProviderStream"):
        return f"[{anime.provider.NAME}] {anime.name} E{stream.episode} [{'dub' if stream.dub else 'sub'}][{stream.resolution}p]"


class SubProcessPlayerBase(PlayerBase):
    def __init__(
        self, player_args_template: List[str], player_path: str, rpc_client=None
    ):
        self._rpc_client = rpc_client
        self._sub_proc = None
        self._player_args_template = player_args_template
        self._player_exec = player_path

    @property
    def rpc_client(self):
        return self._rpc_client

    def play_title(self, anime: "Anime", stream: "ProviderStream"):
        player_cmd = [
            i.format(
                media_title=self._get_media_title(anime, stream), stream_url=stream.url
            )
            for i in self._player_args_template
        ]
        player_cmd.insert(0, self._player_exec)

        if isinstance(self._sub_proc, sp.Popen):
            self.kill_player()

        self._sub_proc = self._open_sproc(player_cmd)

        self._write_hist(anime, stream)
        self._start_dc_presence(anime, stream)

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
