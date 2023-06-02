import os
import subprocess as sp
import sys
from typing import List
from abc import ABC, abstractmethod

from anipy_cli.colors import cprint, colors
from anipy_cli.config import Config
from anipy_cli.history import history
from anipy_cli.misc import dc_presence, Entry


class PlayerBase(ABC):
    @property
    @abstractmethod
    def rpc_client(self):
        pass

    @abstractmethod
    def play_title(self, entry: Entry):
        pass

    @abstractmethod
    def play_file(self, path: str):
        pass

    @abstractmethod
    def wait(self):
        pass

    @abstractmethod
    def kill_player(self):
        pass

    def _start_dc_presence(self, entry: Entry):
        if self.rpc_client:
            dc_media_title = f"{entry.show_name} | {entry.ep}/{entry.latest_ep}"
            dc_presence(dc_media_title, entry.category_url, self.rpc_client)

    @staticmethod
    def _write_hist(entry: Entry):
        history(entry).write_hist()

    @staticmethod
    def _get_media_title(entry: Entry):
        return (
            entry.show_name
            + " - Episode: "
            + str(entry.ep)
            + " - "
            + str(entry.quality)
        )


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

    def play_title(self, entry):
        player_cmd = [
            i.format(media_title=self._get_media_title(entry), **vars(entry))
            for i in self._player_args_template
        ]
        player_cmd.insert(0, self._player_exec)

        if isinstance(self._sub_proc, sp.Popen):
            self.kill_player()

        self._sub_proc = self._open_sproc(player_cmd)

        self._write_hist(entry)
        self._start_dc_presence(entry)

    def play_file(self, path):
        if isinstance(self._sub_proc, sp.Popen):
            self.kill_player()

        player_cmd = [self._player_exec, path]
        self._sub_proc = self._open_sproc(player_cmd)

    def wait(self):
        self._sub_proc.wait()

    def kill_player(self):
        self._sub_proc.kill()

    @staticmethod
    def _open_sproc(player_command: List[str]) -> sp.Popen:
        try:
            if os.name in ("nt", "dos"):
                sub_proc = sp.Popen(player_command)
            else:
                sub_proc = sp.Popen(player_command, stdout=sp.PIPE, stderr=sp.DEVNULL)
        except FileNotFoundError as e:
            cprint(colors.RED, "Error:" + str(e))
            sys.exit()

        return sub_proc
