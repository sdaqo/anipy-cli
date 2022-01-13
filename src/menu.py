#local imports
from src import play, query, url, history, seasonal
import main
import config
from src.colors import colors
#imports
import re
import os
import time
import signal
import sys
import requests
from threading import Thread

options = [
    colors.GREEN + "[n] " + colors.END + "Next Episode",
    colors.GREEN + "[p] " + colors.END + "Previous Episode",
    colors.GREEN + "[r] " + colors.END + "Replay episode",
    colors.GREEN + "[s] " + colors.END + "Select episode",
    colors.GREEN + "[h] " + colors.END + "History selection",
    colors.GREEN + "[a] " + colors.END + "Search for Anime",
    colors.GREEN + "[q] " + colors.END + "Quit"
]


def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')


def kill_subprocess_with_player():
    if os.name in ('nt', 'dos'):
        play.sub_proc.kill()
    else:
        # On linux we cant use .kill(),
        # we have to kill the shell where the sp is running.
        # And if the shell is not running anymore (user closed it)
        # it raises an exception therefore the try/except.
        try:
            os.killpg(os.getpgid(play.sub_proc.pid), signal.SIGTERM)
        except:
            pass


def main_menu(link):
    if type(link) is tuple:
        try:
            requests.get(link[0])
            link = link[0]
        except:
            link = link[1]
    else:
        pass
    clear_console()
    print(colors.GREEN + "Playing: " + colors.RED +
          link.replace(config.gogoanime_url, ""))

    for i in options:
        print(i)

    while True:
        which_option = input("Enter option: " + colors.CYAN)

        if which_option == "n":  # next episode
            episode = ''
            for i in range(4):
                if link[-(i + 1)].isdigit():             
                    episode += link[-(i + 1)]
                else:
                    break
            episode = episode[::-1]

            if episode == seasonal.get_newest_episodes(link):
                print(colors.ERROR + 'No episode after that' + colors.END)
            else:
                kill_subprocess_with_player()
                while True:
                    check = history.done_writing_queue.get()
                    if check == True:
                        break
                    time.sleep(0.3)
                

                episode_in_string_index = link.rfind(episode)
                link = link[:episode_in_string_index] + str(int(episode) + 1)
    
                start_episode(link)
                main_menu(link)

        elif which_option == "p":  # previous episode
            episode = ''
            for i in range(4):
                if link[-(i + 1)].isdigit():             
                    episode += link[-(i + 1)]
                else:
                    break
            episode = episode[::-1]
            
            if episode == "1":
                print(colors.ERROR 
                      + "There is no episode before that." +
                      colors.END)
                pass
            else:
                kill_subprocess_with_player()
                while True:
                    check = history.done_writing_queue.get()
                    if check == True:
                        break
                    time.sleep(0.3)
                
                episode_in_string_index = link.rfind(episode)
                link = link[:episode_in_string_index] + str(int(episode) - 1)
                
                start_episode(link)
                main_menu(link)

        elif which_option == "r":  # replay episode
            kill_subprocess_with_player()
            while True:
                check = history.done_writing_queue.get()
                if check == True:
                    break
                time.sleep(0.3)
            start_episode(link)
            main_menu(link)

        elif which_option == "s":  # select episode
            episode = re.search(r"episode-[0-9]*", link)
            if episode == None:
                episode = ''
                for i in range(4):
                    if link[-(i + 1)].isdigit():             
                        episode += link[-(i + 1)]
                    else:
                        break
                episode = episode[::-1]  
                
                link = link.replace(config.gogoanime_url,
                         "").replace("-" + episode, "")
                link = config.gogoanime_url + "category/" + link
                link = query.episode(link)[1]
            else:
                episode = episode.group(0).replace("episode-", "")
            
                link = link.replace(config.gogoanime_url,
                                "").replace("-episode-" + episode, "")
                link = config.gogoanime_url + "category/" + link
                link = query.episode(link)[0]
        
            time.sleep(5)
            kill_subprocess_with_player()
            while True:
                check = history.done_writing_queue.get()
                if check == True:
                    break
                time.sleep(0.3)
            start_episode(link)
            main_menu(link)

        elif which_option == "h":  # History selection
            kill_subprocess_with_player()
            clear_console()
            picked_history = history.pick_history()
            link_with_episode = picked_history[0]
            resume_seconds = picked_history[1]
            is_history = True
            start_episode(link_with_episode, resume_seconds, is_history)
            main_menu(link_with_episode)

        elif which_option == "a":  # Anime Search
            kill_subprocess_with_player()
            while True:
                check = history.done_writing_queue.get()
                if check == True:
                    break
                time.sleep(0.3)

            search = input(colors.END + "Search for Anime: " + colors.CYAN)
            search_link = query.query(search)
            search_link_with_episode = query.episode(search_link)
            start_episode(search_link_with_episode)
            main_menu(search_link_with_episode)

        elif which_option == "q":  # quit
            kill_subprocess_with_player()
            while True:
                check = history.done_writing_queue.get()
                if check == True:
                    break
                time.sleep(0.2)
            sys.exit()

        else:
            print(colors.ERROR + "Invalid Input" + colors.END)


def start_episode(link, resume_seconds=0, is_history=False):
    try:
        name = link.replace(config.gogoanime_url, '')
    except:
        name = link[0].replace(config.gogoanime_url, '')
    print(colors.GREEN + 'Getting embed url for ' + colors.END + name)
    embed_url = url.get_embed_url(link)
    print(colors.GREEN + 'Getting video url for ' + colors.END + name)
    video_url = url.get_video_url(embed_url[0], link, main.args.quality)
    if is_history == False:
        t1 = Thread(target=play.play,
                    args=(
                        embed_url[0],
                        video_url,
                        embed_url[1],
                        is_history,
                    ))
        t1.start()
    else:
        t1 = Thread(target=play.play,
                    args=(
                        embed_url[0],
                        video_url,
                        embed_url[1],
                        is_history,
                        resume_seconds,
                    ))
        t1.start()

   
