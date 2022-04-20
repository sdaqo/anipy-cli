import argparse


def parse_args():
    parser = argparse.ArgumentParser(
        description="Play Animes from gogoanime in local video-player or Download them."
    )

    parser.add_argument(
        "-q",
        "--quality",
        action="store",
        required=False,
        help="Change the quality of the video, accepts: best, worst or 360, 480, 720 etc.  Default: best",
    )
    parser.add_argument(
        "-H",
        "--history",
        required=False,
        dest="history",
        action="store_true",
        help="Show your history of watched anime",
    )
    parser.add_argument(
        "-d",
        "--download",
        required=False,
        dest="download",
        action="store_true",
        help="Download mode. Download multiple episodes like so: first_number-second_number (e.g. 1-3)",
    )
    parser.add_argument(
        "-D",
        "--delete-history",
        required=False,
        dest="delete",
        action="store_true",
        help="Delete your History.",
    )
    parser.add_argument(
        "-b",
        "--binge",
        required=False,
        dest="binge",
        action="store_true",
        help="Binge mode. Binge multiple episodes like so: first_number-second_number (e.g. 1-3)",
    )
    parser.add_argument(
        "-s",
        "--seasonal",
        required=False,
        dest="seasonal",
        action="store_true",
        help="Seasonal Anime mode. Bulk download or binge watch newest episodes.",
    )

    parser.add_argument(
        "-f",
        "--ffmpeg",
        required=False,
        dest="ffmpeg",
        action="store_true",
        help="Use ffmpeg to download m3u8 playlists, may be more stable but is way slower than internal downloader",
    )
    parser.add_argument(
        "-c",
        "--config",
        required=False,
        dest="config",
        action="store_true",
        help="Print path to the config file.",
    )
    parser.add_argument(
        "-o",
        "--no-kitsu",
        required=False,
        dest="no_kitsu",
        action="store_true",
        help="Turn off search in season. Disables prompting if kitsu is to be searched for anime in specific season.",
    )
    parser.add_argument(
        "-a",
        "--auto-update",
        required=False,
        dest="auto_update",
        action="store_true",
        help="Automatically update and download all Anime in seasonals list from start EP to newest.",
    )

    return parser.parse_args()
