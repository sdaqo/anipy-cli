#!/usr/bin/python3

# This code adds the base directory to the import path
# this allows us to import config.py directly
import sys

sys.path.insert(0, ".")

# local imports
import config
from src import query, play, history, menu, download, url, binge, seasonal
from src.colors import colors
# imports
import argparse, sys
from threading import Thread

my_parser = argparse.ArgumentParser(
    description='Play Animes from gogoanime in local video-player.')
my_parser.add_argument('-q',
                       '--quality',
                       action='store',
                       required=False,
                       help='Pick quality. 1080, 720, 480 etc. / best,worst')
my_parser.add_argument('-H',
                        '--history',
                        required=False,
                        dest="history",
                        action='store_true',
                        help='Play History. History is stored in history/history.txt')
my_parser.add_argument('-d',
                        '--download',
                        required=False,
                        dest='download',
                        action='store_true',
                        help='Download mode. Download multiple episodes like so: first_number-second_number (e.g. 1-3)'
)
my_parser.add_argument('-D',
                       '--delete-history',
                       required=False,
                       dest='delete',
                       action='store_true',
                       help='Delete your History.')
my_parser.add_argument("-b",
                        "--binge",
                        required=False,
                        dest="binge",
                        action="store_true",
                        help="Binge mode. Binge multiple episodes like so: first_number-second_number (e.g. 1-3)",
)
my_parser.add_argument("-s",
                        "--seasonal",
                        required=False,
                        dest="seasonal",
                        action="store_true",
                        help="Seasonal Anime mode. Bulk download or binge watch newest episodes.",
)
# TODO: add argument so `python main.py <Some Anime>` is possible
args = my_parser.parse_args()

if args.delete == True:
    try:
        config.history_file_path.open('w').close()
        print(colors.RED + "Done" + colors.END)

    except FileNotFoundError:
        print(colors.END + "There is no History-File.")

    sys.exit()

if args.download == True:
    download.main_activity()

if args.binge == True:
    binge.main_activity()

if args.seasonal == True:
    seasonal.main_activity()

def main():

    if args.history == False:
        search = input("Search for Anime: " + colors.CYAN)
        link = query.query(search)
        link_with_episode = query.episode(link)
    else:
        history.done_writing_queue.put(True)
        picked_history = history.pick_history()
        link_with_episode = picked_history[0]

    print("getting video urls")
    embed_url = url.get_embed_url(link_with_episode)
    video_url = url.get_video_url(embed_url[0], embed_url[1], args.quality)
    if args.history == False:
        t1 = Thread(target=play.play,
                    args=(
                        embed_url[0],
                        video_url,
                        embed_url[1],
                        args.history,
                    ))
        t1.start()
    else:
        t1 = Thread(target=play.play,
                    args=(
                        embed_url[0],
                        video_url,
                        embed_url[1],
                        args.history,
                        picked_history[1],
                    ))
        t1.start()

    menu.main_menu(embed_url[1])


if __name__ == "__main__":
    main()
