import requests
import sys
import re
from bs4 import BeautifulSoup
from src import query, url, play
from src.colors import colors
import main
from threading import Thread
import os
import signal


def episode_selection(url):
    ep_count = []
    querys = requests.get(url)
    soup = BeautifulSoup(querys.content, "html.parser")
    for link in soup.find_all('a', attrs={'ep_end': re.compile("^ *\d[\d ]*$")}):
        ep_count.append(link.get('ep_end'))

    episode_urls = []

    which_episode = input(colors.END + "Episode " + colors.GREEN + "[1-" +
                          ep_count[-1] + "]" + colors.END + ": " + colors.CYAN)

    list_of_episodes = which_episode.strip().split("-")

    if len(list_of_episodes) == 2:
        try:
            first_number = int(list_of_episodes[0])
            second_number = int(list_of_episodes[1])
        except ValueError:
            print(colors.ERROR + "Invalid Input")

        if first_number in list(range(1, int(ep_count[-1]) + 1)):
            start = first_number
        else:
            print(colors.ERROR + "Your first number is invalid.")
            sys.exit()

        if second_number in list(range(start, int(ep_count[-1]) + 1)):
            end = second_number
        else:
            print(colors.ERROR + "Your second number is invalid.")
            sys.exit()

        for i in list(range(start, end + 1)):
            url_with_episode = [
                url.replace("/category", "") + "-episode-" + str(i),
                url.replace('/category', '') + '-' + str(i)
            ]

            episode_urls.append(url_with_episode)

    elif len(list_of_episodes) == 1:

        if int(which_episode) in list(range(1, int(ep_count[-1]) + 1)):
            which_episode = which_episode
            url = [
                url.replace("/category", "") + "-episode-" + which_episode,
                url.replace('/category', '') + '-' + which_episode]

            episode_urls.append(url)

        else:
            print(colors.ERROR + "Invalid input.")
            sys.exit()
    else:
        print(colors.ERROR + "Invalid input.")

    return episode_urls





def main_activity():

    print(colors.GREEN + "***Binge Mode***" + colors.END)
    search = input("Search for Anime: " + colors.CYAN)
    link = query.query(search)
    episode_urls = episode_selection(link)

    
    t1 = Thread(target=fetch_videos, args=(episode_urls, ))
    t1.start()
    prompt_quit()


def fetch_videos(episode_urls):
    embeded_urls = []

    count = 1
    for j in episode_urls:
        if count == 1:
            first_embed_url = url.get_embed_url(j[0])
            first_video_url = url.get_video_url(
                first_embed_url[0], first_embed_url[1], main.args.quality)

            Thread(
                target=play.play,
                args=(
                    first_embed_url[0],
                    first_video_url,
                    first_embed_url[1],
                    main.args.history,
                ),
            ).start()
        else:
            embeded_urls.append(url.get_embed_url(j))
        count += 1
    video_urls = []
    for x in embeded_urls:
        video_urls.append(url.get_video_url(x[0], x[1], main.args.quality))

    for k, l in zip(video_urls, embeded_urls):
        while play.stop is False:
            pass

        Thread(
            target=play.play,
            args=(
                l[0],
                k,
                l[1],
                main.args.history,
            ),
        ).start()


def prompt_quit():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("Videos being queued in the background, quitting here will terminate all players and queues")

    print(colors.GREEN + "[q] " + colors.END + "Quit")
    which_option = input("Enter option: " + colors.CYAN)
    if which_option == "q":  # quit
        kill_subprocess_with_player()
    else:
        print(colors.ERROR + "Invalid Input" + colors.END)
        prompt_quit()


def kill_subprocess_with_player():
    if os.name in ('nt', 'dos'):
        play.sub_proc.kill()
        os._exit(1)
    else:
        # On linux we cant use .kill(),
        # we have to kill the shell where the sp is running.
        # And if the shell is not running anymore (user closed it)
        # it raises an exception therefore the try/except.
        try:
            os.killpg(os.getpgid(play.sub_proc.pid), signal.SIGTERM)
            os._exit(1)
        except ValueError as e:
            print(e)
