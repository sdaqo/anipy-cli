from src import query, url
import subprocess as sp
import argparse
from threading import Thread

# TODO:
#     [] - add threading for mpv process to be able to do more stuff
#     [] - add more options
#     [] - add downloading


my_parser = argparse.ArgumentParser(description='Play Animes from gogoanime in local video-player.')
my_parser.add_argument('-q', '--quality', action='store', required=False, help='1080, 720, 480 etc. / best,worst')
                        

player = "mpv"


def play(embed_url, video_url):
    player_command = player + " cache=yes " +  '--http-header-fields="Referer: ' + embed_url + '"' + " " + video_url
    sp.run(player_command)

def main():
    args = my_parser.parse_args()
    search = input("Search for Anime: ")
    link = query.query(search)
    embed_url = url.get_embed_url(query.episode(link))
    video_url = url.get_video_url(embed_url)    
    video_url = url.quality(video_url, embed_url, args.quality)
    x = Thread(target=play , args=(embed_url, video_url))
    x.start()
    print("Threading")
if __name__ == "__main__":
    main()
