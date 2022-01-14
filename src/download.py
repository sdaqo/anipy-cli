import requests
import sys
import re
from bs4 import BeautifulSoup
from tqdm import tqdm
from src import query, url
from src.colors import colors
import main
import config


def download(video_url, embed_url, fname):
    resp = requests.get(video_url, headers={'referer': embed_url}, stream=True)
    total = int(resp.headers.get('content-length', 0))
    file_path = config.download_folder_path / f"{fname}.mp4"
    print(colors.CYAN, end='\r') # make bar cyan colored
    try:
        with file_path.open('wb') as file, tqdm(
               desc=fname,
               total=total,
               unit='iB',
               unit_scale=True,
               unit_divisor=1024,
        ) as bar:
            for data in resp.iter_content(chunk_size=1024):
                size = file.write(data)
                bar.update(size)
    except KeyboardInterrupt:
        print( colors.ERROR + 'Interrupted, deleting partially downloaded file.' + colors.END)
        file_path.unlink()

def episode_selection(url):
    ep_count = []
    querys = requests.get(url)
    soup = BeautifulSoup(querys.content, "html.parser")
    for link in soup.find_all('a',
                              attrs={'ep_end': re.compile("^ *\d[\d ]*$")}):
        ep_count.append(link.get('ep_end'))

    episode_urls = []

    which_episode = input(colors.END + "Episode " + colors.GREEN + "[1-" +
                          ep_count[-1] + "]" + colors.END + ": " + colors.CYAN)

    list_of_episodes = which_episode.strip().split("-")

    if len(list_of_episodes) == 2:
        try:
            first_number = int(list_of_episodes[0])
            second_number = int(list_of_episodes[1])
        except:
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
                url.replace('/category', '') + '-' + which_episode
            ]

            episode_urls.append(url)
 
        else:
            print(colors.ERROR + "Invalid input.")
            sys.exit()
    else:
        print(colors.ERROR + "Invalid input.")

    return episode_urls


def main_activity():
    print(colors.GREEN + "***Download Mode***" + colors.END)
    print(colors.GREEN + "Downloads are stored in: " + colors.END +
          str(config.download_folder_path))
    search = input("Search for Anime: " + colors.CYAN)
    link = query.query(search)
    episode_urls = episode_selection(link)
    get_links(episode_urls)    
    sys.exit()    

def get_links(episode_urls):
    # Make the download folder if it doesn't exist already
    try:
        config.download_folder_path.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        print(
            colors.ERROR +
            "You don't have the permissions to write to the download folder.")
    
    names = []
    for i in episode_urls:
        names.append(i[0].replace(config.gogoanime_url, ""))
    

    for p, j in zip(names, episode_urls):
        print(colors.GREEN + 'Getting embed url for ' + colors.END + p)
        embed_url = url.get_embed_url(j) 
        
        print(colors.GREEN + 'Getting video url for ' + colors.END + p)
        video_url = url.get_video_url(embed_url[0], embed_url[1], main.args.quality)
        
        download(video_url, embed_url[0], p)
