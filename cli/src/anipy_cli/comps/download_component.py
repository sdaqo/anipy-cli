from pathlib import Path
from typing import List, Protocol, Tuple
from anipy_cli.arg_parser import CliArgs
from anipy_cli.colors import color, colors
from anipy_cli.config import Config
from anipy_cli.util import DotSpinner, get_download_path

from anipy_api.anime import Anime
from anipy_api.download import Downloader
from anipy_api.provider.base import Episode, LanguageTypeEnum


class SuccessfulEpDownload(Protocol):
    """
    Callback for when an episode successfully downloads
    """

    def __call__(self, anime: Anime, ep: Episode, lang: LanguageTypeEnum):
        """
        Args:
            anime: The relevant anime
            ep: An int/float for the episode
            lang: The language that downloaded
        """
        ...


class DownloadComponent:
    """
    A component used to download anime for
    the ani-py CLI.
    """

    def __init__(self, cliArgs: CliArgs, dl_path: Path) -> None:
        self.options = cliArgs
        self.dl_path = dl_path

    def download_anime(
        self,
        picked: List[Tuple[Anime, LanguageTypeEnum, List[Episode]]],
        after_success_ep: SuccessfulEpDownload = lambda anime, ep, lang: None,
        only_skip_ep_on_err: bool = False,
    ) -> List[Tuple[Anime, Episode]]:
        """
        Attributes:
            picked: The chosen animes to download
            after_success_ep: The code to run when an anime successful downloads
            only_skip_ep_on_err: If we should skip the specific episode on an error. If false, we skip the entire anime.
        """
        with DotSpinner("Starting download...") as s:

            def progress_indicator(percentage: float):
                s.set_text(f"Progress: {percentage:.1f}%")

            def info_display(message: str):
                s.write(f"> {message}")

            def error_display(message: str):
                s.write(color(colors.RED, "! ", message))

            downloader = Downloader(progress_indicator, info_display, error_display)

            failed: List[Tuple[Anime, Episode]] = []

            for anime, lang, eps in picked:
                failed = self.download_episodes(
                    s,
                    downloader,
                    anime,
                    lang,
                    eps,
                    after_success_ep,
                    only_skip_ep_on_err,
                )

            return failed

    def download_episodes(
        self,
        spinner: DotSpinner,
        downloader: Downloader,
        anime: Anime,
        lang: LanguageTypeEnum,
        eps: List[Episode],
        after_success_ep: SuccessfulEpDownload = lambda anime, ep, lang: None,
        only_skip_ep_on_err: bool = False,
    ) -> List[Tuple[Anime, Episode]]:
        fails = []
        for ep in eps:
            try:
                self.download_ep(spinner, downloader, anime, lang, ep)
            except Exception as e:
                if only_skip_ep_on_err:
                    error_msg = f"! Issues downloading episode {ep} of {anime.name}. Skipping..."
                else:
                    error_msg = f"! Issues occurred while downloading the series ${anime.name}. Skipping..."
                spinner.write(
                    color(
                        colors.RED,
                        f"! Error: {e}\n",
                        error_msg,
                    )
                )
                fails.append((anime, ep))
                if only_skip_ep_on_err:
                    continue
                return fails

            after_success_ep(anime, ep, lang)
        return fails

    def download_ep(
        self,
        spinner: DotSpinner,
        downloader: Downloader,
        anime: Anime,
        lang: LanguageTypeEnum,
        ep: Episode,
    ):
        config = Config()

        spinner.set_text(
            "Extracting streams for ",
            colors.BLUE,
            f"{anime.name} ({lang})",
            colors.END,
            " Episode ",
            ep,
            "...",
        )

        stream = anime.get_video(ep, lang, preferred_quality=self.options.quality)

        spinner.write(
            f"> Downloading Episode {stream.episode} of {anime.name} ({lang})"
        )

        spinner.set_text("Downloading...")

        downloader.download(
            stream,
            get_download_path(anime, stream, parent_directory=self.dl_path),
            container=config.remux_to,
            ffmpeg=self.options.ffmpeg or config.ffmpeg_hls,
        )

    @staticmethod
    def serve_download_errors(
        failures: List[Tuple[Anime, Episode]],
        only_skip_ep_on_err: bool = False,
    ):
        if not failures:
            return
        text = ", ".join([f"\n\tEpisode {i[1]} of {i[0].name}" for i in failures])
        extra_info = (
            " (and the remaining episodes in that series)"
            if not only_skip_ep_on_err
            else ""
        )

        print(
            color(
                colors.RED,
                f"! Unable to download the following episodes{extra_info}: {text}",
            )
        )
