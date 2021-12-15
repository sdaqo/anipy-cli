from src import query, url
import subprocess as sp
import argparse

# TODO:
#     [] - add threading for mpv process to be able to do more stuff
#     [] - add more args


my_parser = argparse.ArgumentParser(description='Play Animes from gogoanime in local video-player.')
my_parser.add_argument('-q', '--quality', action='store', required=False, help='1080, 720, 480 etc. / best,worst')
                        

player = "mpv"


def play(embed_url, video_url):
    player_command = player + " " +  '--http-header-fields="Referer: ' + embed_url + '"' + " " + video_url
    sp.run(player_command)

def main():
    args = my_parser.parse_args()
    search = input("Search for Anime: ")
    link = query.query(search)
    embed_url = url.get_embed_url(query.episode(link))
    video_url = url.get_video_url(embed_url)    
    video_url = url.quality(video_url, embed_url, args.quality)
    play(embed_url, video_url)
    
if __name__ == "__main__":
    main()