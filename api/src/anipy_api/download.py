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
    def __call__(self, percentage: float): ...


class InfoCallback(Protocol):
    def __call__(self, message: str): ...


class Downloader:
    def __init__(
        self, progress_callback: ProgressCallback, info_callback: InfoCallback
    ):
        self.progress_callback = progress_callback
        self.info_callback = info_callback

        self._session = requests.Session()

        adapter = HTTPAdapter(max_retries=Retry(connect=3, backoff_factor=0.5))
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)

    @staticmethod
    def _get_valid_pathname(name: str):
        if sys.platform == "win32":
            WIN_INVALID_CHARS = ["\\", "/", ":", "*", "?", "<", ">", "|", '"']
            name = "".join(["" if x in WIN_INVALID_CHARS else x for x in name])

        name = "".join(
            [i for i in name if i.isascii()]
        )  # Verify all chars are ascii (eject if not)

        return name

    def m3u8_download(self, stream: "ProviderStream", download_path: Path) -> Path:
        temp_folder = download_path.parent / "temp"
        temp_folder.mkdir(exist_ok=True)
        download_path = download_path.with_suffix(".ts")

        res = self._session.get(stream.url)
        res.raise_for_status()

        m3u8_content = m3u8.M3U8(res.text, base_uri=urljoin(res.url, "."))

        assert m3u8_content.is_variant is False

        counter = 0

        def download_ts(segment: m3u8.Segment):
            nonlocal counter
            url = urljoin(segment.base_uri, segment.uri)
            fname = temp_folder / self._get_valid_pathname(segment.uri)
            try:
                res = self._session.get(str(url))
                res.raise_for_status()

                with fname.open("wb") as fout:
                    fout.write(res.content)

                counter += 1
                self.progress_callback(counter / len(m3u8_content.segments) * 100)
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
                    self.info_callback(
                        "Download Interrupted, cancelling futures, this may take a while..."
                    )
                    pool_video.shutdown(wait=False, cancel_futures=True)
                    raise

            self.info_callback("Parts Downloaded")

            self.info_callback("Merging Parts...")
            with download_path.open("wb") as merged:
                for segment in m3u8_content.segments:
                    fname = temp_folder / self._get_valid_pathname(segment.uri)
                    if not fname.is_file():
                        raise DownloadError(
                            f"Could not merge, missing a segment of this playlist: {stream.url}"
                        )

                    with fname.open("rb") as mergefile:
                        shutil.copyfileobj(mergefile, merged)

            self.info_callback("Merge Finished")
            shutil.rmtree(temp_folder)

            return download_path
        except KeyboardInterrupt:
            self.info_callback("Download Interrupted, deleting partial file.")
            download_path.unlink(missing_ok=True)
            shutil.rmtree(temp_folder)
            raise

    def mp4_download(self, stream: "ProviderStream", download_path: Path) -> Path:
        r = self._session.get(stream.url, stream=True)
        total = int(r.headers.get("content-length", 0))
        try:
            file_handle = download_path.with_suffix(".mp4").open("w")
            for data in r.iter_content(chunk_size=1024):
                size = file_handle.write(data)
                self.progress_callback(size / total * 100)
        except KeyboardInterrupt:
            self.info_callback("Download Interrupted, deleting partial file.")
            download_path.unlink()
            raise

        self.info_callback("Download finished.")

        return download_path.with_suffix(".mp4")

    def ffmpeg_download(self, stream: "ProviderStream", download_path: Path) -> Path:
        ffmpeg = FFmpeg(executable="ffprobe").input(
            stream.url, print_format="json", show_format=None
        )
        meta = json.loads(ffmpeg.execute())
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

        @ffmpeg.on("progress")
        def on_progress(progress: Progress):
            self.progress_callback(progress.time.total_seconds() / duration * 100)

        try:
            ffmpeg.execute()
        except KeyboardInterrupt:
            self.info_callback("interrupted deleting partially downloaded file")
            download_path.unlink()
            raise

        return download_path

    def download(
        self,
        stream: "ProviderStream",
        download_path: Path,
        container: Optional[str] = None,
        ffmpeg: bool = False,
    ) -> Path:
        download_path.parent.mkdir(parents=True, exist_ok=True)

        for p in download_path.parent.iterdir():
            if p.with_suffix("").name == download_path.name:
                self.info_callback("Episode is already downloaded, skipping")
                return p

        if "m3u8" in stream.url:
            if ffmpeg:
                download_path = download_path.with_suffix(container or ".mp4")
                self.info_callback("Using FFMPEG downloader")
                self.info_callback(f"Saving to a {container or '.mp4'} container")
                path = self.ffmpeg_download(stream, download_path)
            else:
                self.info_callback("Using internal M3U8 downloader")
                path = self.m3u8_download(stream, download_path)
        elif "mp4" in stream.url:
            self.info_callback("Using internal MP4 downloader")
            path = self.mp4_download(stream, download_path.with_suffix(".mp4"))
        else:
            self.info_callback(
                "No fitting downloader available for stream, using FFMPEG downloader as fallback"
            )
            path = self.ffmpeg_download(stream, download_path)

        if container:
            if container == path.suffix:
                return path
            self.info_callback(f"Remuxing to {container} container")
            new_path = path.with_suffix(container)
            download = self.ffmpeg_download(
                ProviderStream(
                    str(path), stream.resolution, stream.episode, stream.language
                ),
                new_path,
            )
            path.unlink()
            return download

        return path