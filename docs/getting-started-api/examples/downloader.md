## Downloading 

When downloading, you use the [Downloader][anipy_api.download.Downloader] class, it can handle various stream formats.
When downloading you can choose between several download methods:

- [download][anipy_api.download.Downloader.download]: This method is just a generic method that supports m3u8, mp4 and many more stream formats. It assumes ffmpeg is installed on the machine please look at the [reference][anipy_api.download.Downloader.download] for more info.
- [m3u8_download][anipy_api.download.Downloader.m3u8_download]: Download a m3u8 playlist.
- [mp4_download][anipy_api.download.Downloader.mp4_download]: Download a mp4 stream.
- [ffmpeg_download][anipy_api.download.Downloader.ffmpeg_download]: Download any stream supported by [ffmpeg](https://ffmpeg.org). This requires ffmpeg to be installed on the system!


```python
from pathlib import Path

from anipy_api.download import Downloader
from anipy_api.provider import LanguageTypeEnum

anime = ...
stream = anime.get_video(1, LanguageTypeEnum.SUB, preferred_quality=1080)

def progress_callback(percentage: float): # (1)
    print(f"Progress: {percentage:.1f}%", end="\r")

def info_callback(message: str): # (2)
    print(f"Message from the downloader: {message}")

def error_callback(message: str): # (3)
    s.write(f"Soft error from the downloader: {message}")


downloader = Downloader(progress_callback, info_callback, error_callback)
download_path = downloader.download( # (4)
    stream=stream,
    download_path=Path("~/Downloads"),
    container=".mkv", # (5)
    maxRetry=3 # (6)
    ffmpeg=False # (7)
)
```

1. The progress callback gets called on progress-related tasks like downloading or remuxing in the Downloader.
2. The info callback gets called on information coming from the downloader.
3. The error callback gets called on non-fatal errors coming from the downloader.
4. Always make sure to use the resulting path of the methods, because they may alter the path passed to them! This also applies to the other download methods!
5. With optional container argument the downloader will use ffmpeg to remux the video if the container is not the same as specified, note that this will trigger the `progress_callback` for remuxing!
6. The downloader will always try the download three times. The retry count can be adjusted here; any errors encountered use the `error_callback`.
7. For the other arguments check the [reference][anipy_api.download.Downloader.download]!
