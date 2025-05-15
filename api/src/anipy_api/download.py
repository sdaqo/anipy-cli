import json
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional, Protocol
from urllib.parse import urljoin

import m3u8
import requests
from ffmpeg import FFmpeg, Progress
from requests.adapters import HTTPAdapter, Retry

from anipy_api.error import DownloadError
from anipy_api.provider import ProviderStream


class ProgressCallback(Protocol):
    """Callback that accepts a percentage argument."""

    def __call__(self, percentage: float):
        """
        Args:
            percentage: Percentage argument passed to the callback
        """
        ...


class InfoCallback(Protocol):
    """Callback that accepts a message argument."""

    def __call__(self, message: str):
        """
        Args:
            message: Message argument passed to the callback
        """
        ...


class PostDownloadCallback(Protocol):
    """Callback that accepts a message argument."""

    def __call__(self, path: Path, stream: "ProviderStream"):
        """

        Args:
            path: Path of the resulting download, passed to the callback
            stream: ProviderStream object passed to the callback
        """
        ...


class Downloader:
    """Downloader class to download streams retrieved by the Providers."""

    def __init__(
        self,
        progress_callback: Optional[ProgressCallback] = None,
        info_callback: Optional[InfoCallback] = None,
        soft_error_callback: Optional[InfoCallback] = None,
    ):
        """__init__ of Downloader.

        Args:
            progress_callback: A callback with an percentage argument, that gets called on download progress.
            info_callback: A callback with an message argument, that gets called on certain events.
            soft_error_callback: A callback with a message argument, when certain events cause a non-fatal error (if none given, alternative fallback is info_callback).
        """
        self._progress_callback: ProgressCallback = progress_callback or (
            lambda percentage: None
        )
        self._info_callback: InfoCallback = info_callback or (lambda message: None)
        self._soft_error_callback: InfoCallback = (
            soft_error_callback or info_callback or (lambda message: None)
        )

        self._session = requests.Session()

        adapter = HTTPAdapter(max_retries=Retry(connect=3, backoff_factor=0.5))
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)

    @staticmethod
    def _get_valid_pathname(name: str):
        if sys.platform == "win32":
            INVALID_CHARS = ["\\", "/", ":", "*", "?", "<", ">", "|", '"', "."]
        else:
            INVALID_CHARS = [".", "/"]

        name = "".join(
            [i for i in name if i.isascii() and i not in INVALID_CHARS]
        )  # Verify all chars are ascii (eject if not)

        return name

    def m3u8_download(self, stream: "ProviderStream", download_path: Path) -> Path:
        """Download a m3u8/hls stream to a specified download path in a ts container.

        The suffix of the download path will be replaced (or added) with
        ".ts", use the path returned instead of the passed path.

        Args:
            stream: The m3u8/hls stream
            download_path: The path to save the downloaded stream to

        Raises:
            DownloadError: Raised on download error

        Returns:
            The path with a ".ts" suffix
        """
        temp_folder = download_path.parent / "temp"
        temp_folder.mkdir(exist_ok=True)
        download_path = download_path.with_suffix(".ts")
        res = self._session.get(stream.url, headers={"Referer": stream.referrer})
        res.raise_for_status()

        m3u8_content = m3u8.M3U8(res.text, base_uri=urljoin(res.url, "."))

        assert m3u8_content.is_variant is False

        counter = 0

        def download_ts(segment: m3u8.Segment):
            nonlocal counter
            url = urljoin(segment.base_uri, segment.uri)
            segment_uri = Path(segment.uri)
            fname = (
                temp_folder / self._get_valid_pathname(segment_uri.stem)
            ).with_suffix(segment_uri.suffix)
            try:
                res = self._session.get(str(url), headers={"Referer": stream.referrer})
                res.raise_for_status()

                with fname.open("wb") as fout:
                    fout.write(res.content)

                counter += 1
                self._progress_callback(counter / len(m3u8_content.segments) * 100)
            except Exception as e:
                # TODO: This gets ignored, because it's in a seperate thread...
                raise DownloadError(
                    f"Encountered this error while downloading: {str(e)}"
                )

        try:
            with ThreadPoolExecutor(max_workers=12) as pool_video:
                futures = [
                    pool_video.submit(download_ts, s) for s in m3u8_content.segments
                ]
                try:
                    for future in as_completed(futures):
                        future.result()
                except KeyboardInterrupt:
                    self._info_callback(
                        "Download Interrupted, cancelling futures, this may take a while..."
                    )
                    pool_video.shutdown(wait=False, cancel_futures=True)
                    raise

            self._info_callback("Parts Downloaded")

            self._info_callback("Merging Parts...")
            with download_path.open("wb") as merged:
                for segment in m3u8_content.segments:
                    uri = Path(segment.uri)
                    fname = (
                        temp_folder / self._get_valid_pathname(uri.stem)
                    ).with_suffix(uri.suffix)
                    if not fname.is_file():
                        raise DownloadError(
                            f"Could not merge, missing a segment of this playlist: {stream.url}"
                        )

                    with fname.open("rb") as mergefile:
                        shutil.copyfileobj(mergefile, merged)

            self._info_callback("Merge Finished")
            shutil.rmtree(temp_folder)

            return download_path
        except KeyboardInterrupt:
            self._info_callback("Download Interrupted, deleting partial file.")
            download_path.unlink(missing_ok=True)
            shutil.rmtree(temp_folder)
            raise

    def mp4_download(self, stream: "ProviderStream", download_path: Path) -> Path:
        """Download a mp4 stream to a specified download path.

        The suffix of the download path will be replaced (or added)
        with ".mp4", use the path returned instead of the passed path.

        Args:
            stream: The mp4 stream
            download_path: The path to download the stream to

        Returns:
            The download path with a ".mp4" suffix
        """
        r = self._session.get(
            stream.url, stream=True, headers={"Referer": stream.referrer}
        )
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        try:

            with download_path.with_suffix(".mp4").open("wb") as file_handle:
                downloaded_size = 0
                for data in r.iter_content(chunk_size=1024):
                    downloaded_size += file_handle.write(data)
                    self._progress_callback(downloaded_size / total * 100)

        except KeyboardInterrupt:
            self._info_callback("Download Interrupted, deleting partial file.")
            download_path.unlink()
            raise

        self._info_callback("Download finished.")

        return download_path.with_suffix(".mp4")

    def ffmpeg_download(self, stream: "ProviderStream", download_path: Path) -> Path:
        """Download a stream with FFmpeg, FFmpeg needs to be installed on the
        system. FFmpeg will be able to handle about any stream and it is also
        able to remux the resulting video. By changing the suffix of the
        `download_path` you are able to tell ffmpeg to remux to a specific
        container.

        Args:
            stream: The stream
            download_path: The path to download to including a specific suffix.

        Returns:
            The download path, this should be the same as the
            passed one as ffmpeg will remux to about any container.
        """

        ffprobe = (
            FFmpeg(executable="ffprobe")
            .option("v", 0)
            .option("of", "json")
            .option("show_program_version")
        )
        version = json.loads(ffprobe.execute())
        version = [
            int(''.join(c for c in v if c.isdigit())) for v in version["program_version"]["version"].split("-")[0].split(".")
        ]

        if len(version) < 3:
            version.append(0)

        major_v, minor_v, patch_v = version

        extension_picky = major_v >= 7 and minor_v >= 1 and patch_v >= 1

        ffprobe = FFmpeg(executable="ffprobe").input(
            stream.url, print_format="json", show_format=None
        )

        if stream.referrer:
            ffprobe.option("headers", f"Referer: {stream.referrer}")

        if extension_picky:
            ffprobe.option("extension_picky", 0)

        meta = json.loads(ffprobe.execute())
        duration = float(meta["format"]["duration"])

        ffmpeg = (
            FFmpeg()
            .option("y")
            .option("v", "warning")
            .option("stats")
            .input(stream.url)
            .output(
                download_path,
                {"c:v": "copy", "c:a": "copy", "c:s": "mov_text"},
            )
        )

        if stream.referrer:
            ffmpeg.option("headers", f"Referer: {stream.referrer}")

        if extension_picky:
            ffmpeg.option("extension_picky", 0)

        @ffmpeg.on("progress")
        def on_progress(progress: Progress):
            self._progress_callback(progress.time.total_seconds() / duration * 100)

        try:
            ffmpeg.execute()
        except KeyboardInterrupt:
            self._info_callback("interrupted deleting partially downloaded file")
            download_path.unlink()
            raise

        return download_path

    def download_sub(self, stream: "ProviderStream", download_path: Path):
        if not stream.subtitle:
            return

        download_path.parent.mkdir(parents=True, exist_ok=True)
        self._info_callback("Downloading external subs")
        for s in stream.subtitle.values():
            res = self._session.get(s.url, headers={"Referer": stream.referrer})
            suffix = f".{s.shortcode}.{s.codec}"
            path = download_path.with_suffix(suffix)
            with path.open("w", encoding="utf-8") as fp:
                fp.write(res.content.decode())

    def download(
        self,
        stream: "ProviderStream",
        download_path: Path,
        container: Optional[str] = None,
        ffmpeg: bool = False,
        max_retry: int = 3,
        post_dl_cb: Optional[PostDownloadCallback] = None,
    ) -> Path:
        """Generic download function that determines the best way to download a
        specific stream and downloads it. The suffix should be omitted here,
        you can instead use the `container` argument to remux the stream after
        the download, note that this will trigger the `progress_callback`
        again. This function assumes that ffmpeg is installed on the system,
        because if the stream is neither m3u8 or mp4 it will default to
        [ffmpeg_download][anipy_api.download.Downloader.ffmpeg_download].

        Args:
            stream: The stream to download
            download_path: The path to download the stream to.
            container: The container to remux the video to if it is not already
                correctly muxed, the user must have ffmpeg installed on the system.
                Containers may include all containers supported by FFmpeg e.g. ".mp4", ".mkv" etc...
            ffmpeg: Wheter to automatically default to
                [ffmpeg_download][anipy_api.download.Downloader.ffmpeg_download] for m3u8/hls streams.
            max_retry: The amount of times the API can retry the download
            post_dl_cb: Called when completing download, not called when file already exsists

        Returns:
            The path of the resulting file
        """
        curr_exc: Exception | None = None
        post_dl_cb = post_dl_cb or (lambda path, stream: None)
        for i in range(max_retry):
            try:
                path = self._download_single_try(
                    stream, download_path, post_dl_cb, container, ffmpeg
                )
                return path
            except DownloadError as e:
                self._soft_error_callback(str(e))
                curr_exc = e
            except Exception as e:
                self._soft_error_callback(f"An error occurred during download: {e}")
                curr_exc = e
            self._soft_error_callback(f"{max_retry-i-1} retries remain")

        # Impossible, but to make the type
        # checker happy
        if curr_exc is None:
            raise DownloadError("Unknown error occurred")
        # If retrying doesn't work, double it and
        # give it to the next exception handler
        raise curr_exc

    def _download_single_try(
        self,
        stream: "ProviderStream",
        download_path: Path,
        post_dl_cb: PostDownloadCallback,
        container: Optional[str] = None,
        ffmpeg: bool = False,
    ) -> Path:
        download_path.parent.mkdir(parents=True, exist_ok=True)

        for p in download_path.parent.iterdir():
            if p.with_suffix("").name == download_path.name:
                self._info_callback("Episode is already downloaded, skipping")
                return p

        self.download_sub(stream, download_path)

        if "m3u8" in stream.url:
            if ffmpeg:
                download_path = download_path.with_suffix(container or ".mp4")
                self._info_callback("Using FFMPEG downloader")
                self._info_callback(f"Saving to a {container or '.mp4'} container")
                path = self.ffmpeg_download(stream, download_path)
            else:
                self._info_callback("Using internal M3U8 downloader")
                path = self.m3u8_download(stream, download_path)
        elif "mp4" in stream.url:
            self._info_callback("Using internal MP4 downloader")
            path = self.mp4_download(stream, download_path.with_suffix(".mp4"))
        else:
            self._info_callback(
                "No fitting downloader available for stream, using FFMPEG downloader as fallback"
            )
            path = self.ffmpeg_download(
                stream, download_path.with_suffix(container or ".mp4")
            )

        if container:
            if container == path.suffix:
                post_dl_cb(path, stream)
                return path
            self._info_callback(f"Remuxing to {container} container")
            new_path = path.with_suffix(container)
            download = self.ffmpeg_download(
                ProviderStream(
                    str(path),
                    stream.resolution,
                    stream.episode,
                    stream.language,
                ),
                new_path,
            )
            path.unlink()
            post_dl_cb(download, stream)
            return download

        post_dl_cb(path, stream)
        return path
