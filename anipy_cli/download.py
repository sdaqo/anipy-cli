import json
import re
import urllib
from pathlib import Path

import m3u8
import requests
import shutil
import sys
from tqdm import tqdm
from requests.adapters import HTTPAdapter, Retry
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlsplit
from better_ffmpeg_progress import FfmpegProcess

from .misc import response_err, error, keyboard_inter
from .colors import colors
from . import config


class download:
    """
    Download Class.
    A entry with all fields is required.
    """

    def __init__(self, entry, ffmpeg=False) -> None:
        self._m3u8_content = None
        self.session = None
        self.entry = entry
        self.ffmpeg = ffmpeg
        self.headers = {"referer": self.entry.embed_url}

    def download(self):
        self.show_folder = config.download_folder_path / f"{self.entry.show_name}"
        config.download_folder_path.mkdir(exist_ok=True)
        self.show_folder.mkdir(exist_ok=True)
        self.session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.headers.update(self.headers)

        fname = f"{self.entry.show_name}_{self.entry.ep}.mp4"
        dl_path = self.show_folder / fname

        if dl_path.is_file():
            print("-" * 20)
            print(
                f"{colors.GREEN}Skipping Already Existing:{colors.RED} {self.entry.show_name} EP: {self.entry.ep} - {self.entry.quality} {colors.END}"
            )
            return

        print("-" * 20)
        print(
            f"{colors.CYAN}Downloading:{colors.RED} {self.entry.show_name} EP: {self.entry.ep} - {self.entry.quality} {colors.END}"
        )

        if "m3u8" in self.entry.stream_url:
            print(f"{colors.CYAN}Type:{colors.RED} m3u8")
            if self.ffmpeg or config.ffmpeg_hls:
                print(f"{colors.CYAN}Downloader:{colors.RED} ffmpeg")
                self.ffmpeg_dl()
                return

            print(f"{colors.CYAN}Downloader:{colors.RED} internal")
            self.multithread_m3u8_dl()
        elif "mp4" in self.entry.stream_url:
            print(f"{colors.CYAN}Type:{colors.RED} mp4")
            self.mp4_dl(self.entry.stream_url)

    def ffmpeg_dl(self):
        config.user_files_path.mkdir(exist_ok=True)
        config.ffmpeg_log_path.mkdir(exist_ok=True)
        fname = f"{self.entry.show_name}_{self.entry.ep}.mp4"

        dl_path = self.show_folder / fname

        ffmpeg_process = FfmpegProcess(
            [
                "ffmpeg",
                "-headers",
                f"referer:{self.entry.embed_url}",
                "-i",
                self.entry.stream_url,
                "-vcodec",
                "copy",
                "-acodec",
                "copy",
                "-scodec",
                "mov_text",
                "-y",
                str(dl_path),
            ]
        )

        try:
            ffmpeg_process.run(
                ffmpeg_output_file=str(
                    config.ffmpeg_log_path / fname.replace("mp4", "log")
                )
            )
            print(f"{colors.CYAN}Download finished.")
        except KeyboardInterrupt:
            error("interrupted deleting partially downloaded file")
            fname.unlink()

    def ffmpeg_merge(self, input_file):
        config.user_files_path.mkdir(exist_ok=True)
        config.ffmpeg_log_path.mkdir(exist_ok=True)
        fname = f"{self.entry.show_name}_{self.entry.ep}.mp4"

        dl_path = self.show_folder / fname

        ffmpeg_process = FfmpegProcess(
            [
                "ffmpeg",
                "-i",
                str(input_file),
                "-vcodec",
                "copy",
                "-acodec",
                "copy",
                "-scodec",
                "mov_text",
                "-c",
                "copy",
                str(dl_path),
            ]
        )

        try:
            print(f"{colors.CYAN}Merging Parts using ffmpeg...")
            ffmpeg_process.run(
                ffmpeg_output_file=str(
                    config.ffmpeg_log_path / fname.replace("mp4", "log")
                )
            )
            print(f"{colors.CYAN}Merge finished.")
        except KeyboardInterrupt:
            error("interrupted deleting partially downloaded file")
            fname.unlink()

    def mp4_dl(self, dl_link):
        """

        :param dl_link:
        :type dl_link:
        :return:
        :rtype:
        """
        r = self.session.get(dl_link, headers=self.headers, stream=True)
        response_err(r, dl_link)
        total = int(r.headers.get("content-length", 0))
        fname = self.show_folder / f"{self.entry.show_name}_{self.entry.ep}.mp4"
        try:
            with fname.open("wb") as out_file, tqdm(
                desc=self.entry.show_name,
                total=total,
                unit="iB",
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
                for data in r.iter_content(chunk_size=1024):
                    size = out_file.write(data)
                    bar.update(size)
        except KeyboardInterrupt:
            error("interrupted deleting partially downloaded file")
            fname.unlink()

        print(f"{colors.CYAN}Download finished.")

    def download_ts(self, m3u8_segments):
        self.counter += 1
        uri = urllib.parse.urljoin(m3u8_segments.base_uri, m3u8_segments.uri)
        if not self._is_url(uri):
            return

        filename = self._get_filename(uri, self.temp_folder)
        headers = self.headers

        print(
            f"{colors.CYAN}Downloading Part: {self.counter}/{self.segment_count}",
            end="",
        )
        print("\r", end="")

        try:
            with self.session.get(
                uri, timeout=10, headers=headers, stream=False
            ) as response:

                if response.status_code == 416:
                    return

                response.raise_for_status()

                with open(filename, "wb") as fout:
                    fout.write(response.content)

        except Exception as e:
            exit(e.__str__())

    def multithread_m3u8_dl(self):
        """
        Multithread download
        function for m3u8 links.
        - Creates show and temp folder
        - Starts ThreadPoolExecutor instance
          and downloads all ts links
        - Merges ts files
        - Delets temp folder

        :return:
        :rtype:
        """

        self.temp_folder = self.show_folder / f"{self.entry.ep}_temp"
        self.temp_folder.mkdir(exist_ok=True)
        self.counter = 0

        self._m3u8_content = self._download_m3u8(
            self.entry.stream_url, 10, self.headers
        )
        assert self._m3u8_content.is_variant is False
        self.segment_count = len(self._m3u8_content.segments)
        try:
            with ThreadPoolExecutor(60) as pool:
                pool.map(self.download_ts, self._m3u8_content.segments)
            self._download_key()

        except KeyboardInterrupt:
            shutil.rmtree(self.temp_folder)
            keyboard_inter()
            sys.exit()
        input_file = self._dump_m3u8()

        print(f"\n{colors.CYAN}Parts Downloaded")
        self.ffmpeg_merge(input_file)
        print(f"\n{colors.CYAN}Parts Merged")
        shutil.rmtree(self.temp_folder)

    def _download_m3u8(self, uri, timeout, headers):
        if self._is_url(uri):
            resp = self.session.get(uri, timeout=timeout, headers=self.headers)
            resp.raise_for_status()
            raw_content = resp.content.decode(resp.encoding or "utf-8")
            base_uri = urllib.parse.urljoin(uri, ".")
        else:
            with open(uri) as fin:
                raw_content = fin.read()
                base_uri = Path(uri)
        content = m3u8.M3U8(raw_content, base_uri=base_uri)

        # sort
        sorted_content_playlist = sorted(
            content.playlists, key=lambda x: x.stream_info.bandwidth, reverse=True
        )

        if content.is_variant:
            for index, playlist in enumerate(sorted_content_playlist):
                print(
                    "Selected Quality: {}\n"
                    "Playlist Index: {}\n"
                    "Resolution at this index: {}\n\n".format(
                        self.entry.quality, index, playlist.stream_info.resolution
                    )
                )
                if (
                    "auto" in self.entry.quality and index == 0
                ) or self.entry.quality in playlist.stream_info.resolution:
                    try:
                        chosen_uri = content.playlists[index].uri
                        if not self._is_url(chosen_uri):
                            chosen_uri = urllib.parse.urljoin(
                                content.base_uri, chosen_uri
                            )
                        return self._download_m3u8(chosen_uri, timeout, headers)

                    except (ValueError, IndexError):
                        exit("Failed to get stream for chosen quality")

        return content

    def _dump_m3u8(self):
        for index, segment in enumerate(self._m3u8_content.segments):
            self._m3u8_content.segments[index].uri = self._get_filename(
                segment.uri, self.temp_folder
            )

        filename = self._get_filename("master.m3u8", self.temp_folder)
        print("File Name for local m3u8 file: {}\n\n".format(filename))
        self._m3u8_content.dump(filename)
        return filename

    def _download_key(self):
        for key in self._m3u8_content.keys:
            if key:
                uri = key.absolute_uri
                filename = self._get_filename(uri, self.show_folder)

                with self.session.get(
                    uri, timeout=10, headers=self.headers
                ) as response:
                    response.raise_for_status()
                    with open(filename, "wb") as fout:
                        fout.write(response.content)

                key.uri = filename.__str__().replace(
                    "\\", "/"
                )  # ffmpeg error when using \\ in windows

    @staticmethod
    def _is_url(uri):
        return re.match(r"https?://", uri) is not None

    @staticmethod
    def _get_filename(uri, directory):
        basename = urllib.parse.urlparse(uri).path.split("/")[-1]
        filename = Path("{}/{}".format(directory, basename)).__str__()
        return filename
