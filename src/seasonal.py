import sys
from bs4 import BeautifulSoup
import re
import requests, os
import config
from src import query, download, binge
from src.colors import colors

options = [
    colors.GREEN + "[a] " + colors.END + "Add Anime",
    colors.GREEN + "[e] " + colors.END + "Delete one anime from seasonals",
    colors.GREEN + "[l] " + colors.END + "List animes in seasonals file",
    colors.GREEN + "[d] " + colors.END + "Download newest episodes",
    colors.GREEN + "[w] " + colors.END + "Binge watch newest episodes",
    colors.GREEN + "[q] " + colors.END + "Quit"
]


def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def add_to_seasonals(link):

    try:
        config.history_file_path.parent.mkdir(parents=True, exist_ok=True)
        config.seasonal_file_path.touch(exist_ok=True)
    except PermissionError:
        print(
            "Unable to write/read to where seasonals file is suposed to be due to permissions."
        )
        sys.exit(1)
    
    with config.seasonal_file_path.open('r') as seasonal_file:
        data = seasonal_file.readlines()
    
    in_data = False 

    for i in data:
      if link in i:
         in_data = True
         break
      else:
         pass
    
    if in_data == False:
        with open(config.seasonal_file_path, 'a') as f:
            f.write(link + '\n')
    else:
        print(colors.ERROR + 'Anime already in seasonal.txt file')

def delete_seasonal():
    clear_console()
    
    with config.seasonal_file_path.open('r') as seasonal_file:
        links = seasonal_file.readlines()


    list_index = 1

    for j in links:
        if list_index % 2 == 0:
            color = colors.YELLOW
        else:
            color = ""
        anime =  j.replace("category/", "").replace(config.gogoanime_url, '').replace('\n', '')
        anime = re.sub(r'\#.*', '', anime)
        
        print(colors.GREEN + "[" + str(list_index) + "]" + colors.END + " " +
              f"{color}" + anime + colors.END)
        list_index += 1
    
 
    while True:
        which_anime = input("Enter Number: " + colors.CYAN)

        try:
            links.pop(int(which_anime) - 1)
            break
        except:
            print(colors.ERROR + "Invalid Input")
    
    with config.seasonal_file_path.open('w') as seasonal_file:
        for i in links: 
            seasonal_file.write(i)


def list_seasonals():
    links = read_seasonal()[0]

    for i in links:
        anime = i.replace("category/", "").replace(config.gogoanime_url, '').replace('\n', '')
        anime = re.sub(r'\#.*', '', anime)
        print('-> ' + anime)

    input(colors.GREEN + 'Press Enter-Key to get back to the menu.' + colors.END)    

def read_seasonal():
    
    try:
        with config.seasonal_file_path.open('r') as seasonal_file:
            data = seasonal_file.readlines()
        
        links = []
        previous_links = []

        for i in data:
            i = i.split("#")
            links.append(i[0])
            try:
                previous_links.append(i[1].replace("\n", ""))
            except:
                previous_links.append(' ')

    except Exception as e:
        print(e)
        print('\n' + colors.ERROR + 'Probably there is no seasonals.txt yet. Add animes to create one.')
        sys.exit()

    return links, previous_links



def get_new_episodes(url):
    ep_count = []
    querys = requests.get(url)
    soup = BeautifulSoup(querys.content, "html.parser")
    for link in soup.find_all('a',
                              attrs={'ep_end': re.compile("^ *\d[\d ]*$")}):
        ep_count.append(link.get('ep_end'))
    
    newest_ep = ep_count[-1]
    
    episode_urls = [
    url.replace("/category", "") + "-episode-" + newest_ep,
    url.replace('/category', '') + '-' + newest_ep
    ]
    
    episode_urls[0] = episode_urls[0].replace('\n', '')
    episode_urls[1] = episode_urls[1].replace('\n', '')

    return episode_urls
   
def compare():
    seasonal_file = read_seasonal()    

    ep_urls = []
    for i in seasonal_file[0]:
        i = get_new_episodes(i)
        ep_urls.append(i)
    
    already_watched = []
    not_watched = []

    for i, u in zip(seasonal_file[1], ep_urls):
        if i == u[0]:
            already_watched.append(u)
        else:
            not_watched.append(u)

    return already_watched, not_watched


def start_action(is_watching: bool):
    episode_urls_original = compare()
    if not episode_urls_original[0]:
        episode_urls = episode_urls_original[1]
        pass
    else:
        print(colors.GREEN + 'Already downloaded or watched: ' + colors.END)
        for i in episode_urls_original[0]:
            print('-> ' + i[0].replace(config.gogoanime_url, ''))
    
        confirm_exclude = input(
            colors.GREEN 
            + f'Do you want to exclude these from {"watching" if is_watching else "downloading"}?' 
            + colors.RED + ' (y/N): ' + colors.CYAN)
        
        if confirm_exclude == 'y' or confirm_exclude == 'Y':
            episode_urls = episode_urls_original[1]
        else:
            if not episode_urls_original[1]:
                episode_urls = episode_urls_original[0]
            else:
                episode_urls = episode_urls_original[0] + episode_urls_original[1]

    print(colors.GREEN + f'{"Watching" if is_watching else "Downloading"}: ' + colors.END)
    for i in episode_urls:
        print('-> ' + i[0].replace(config.gogoanime_url, ''))
    
    confirm = input(
         colors.GREEN 
        + f'Do you want to {"watch" if is_watching else "download"} these/this episode(s)?' 
        + colors.RED + ' (y/N): ' + colors.CYAN)
    
    if confirm == 'y' or confirm == 'Y':
        if is_watching == False:
            download.get_links(episode_urls)
            
            with config.seasonal_file_path.open('r') as seasonal_file:
                data = seasonal_file.readlines()
        
            if not episode_urls_original[1]:
                pass
            else:
                episode_urls = episode_urls_original[0] + episode_urls_original[1]
        
            temp_data = []
            for i, u in zip(data, episode_urls):
                i = i.split('#')    
                temp_data.append(
                    i[0].replace('\n', '') + '#' + u[0] + '\n')
            with config.seasonal_file_path.open('w') as seasonal_file:
                for i in temp_data:
                    seasonal_file.write(i)
        
            sys.exit()
        else:
            
            with config.seasonal_file_path.open('r') as seasonal_file:
                data = seasonal_file.readlines()
        
            if not episode_urls_original[1]:
                episode_urls2 = episode_urls
            else:
                episode_urls2 = episode_urls_original[0] + episode_urls_original[1]
        
            temp_data = []
            for i, u in zip(data, episode_urls2):
                i = i.split('#')    
                temp_data.append(
                    i[0].replace('\n', '') + '#' + u[0] + '\n')
            with config.seasonal_file_path.open('w') as seasonal_file:
                for i in temp_data:
                    seasonal_file.write(i)
            
            binge.start_watching(episode_urls)
    else:
        print(colors.GREEN + 'Ok exiting now')
        sys.exit()

def menu():
    
    for i in options:
        print(i)
    
    while True:
       
        which_option = input("Enter Option: " + colors.CYAN)
        print(colors.END, end='\r')

        if which_option == 'a': # add anime to seasonals
            search_input = input('Search Anime: ')    
            link = query.query(search_input)
            add_to_seasonals(link)
            clear_console()
            print(colors.GREEN + 'Added anime.' + colors.END)
            menu()
    

        elif which_option == 'e': # delete one anime from seasonals 
            delete_seasonal()
            clear_console()
            menu()

        elif which_option == 'l':
            list_seasonals()
            clear_console()
            menu()


        elif which_option == 'd': # download newest episodes
            seasonal_file = read_seasonal()    
            if not seasonal_file[0] or not seasonal_file[1]:
                print(colors.ERROR + 'No animes to download, add some.' + colors.END)
                
            else:
                start_action(False)

        elif which_option == 'w':
            seasonal_file = read_seasonal()    
            if not seasonal_file[0] or not seasonal_file[1]:
                print(colors.ERROR + 'No animes to watch, add some.' + colors.END)
                
            else:
                start_action(True)

        elif which_option == 'q':
            sys.exit()

        else:
            print(colors.ERROR + 'Invalid input')



        

def main_activity():
    print(colors.GREEN + '***Seasonal Mode***')
    print(colors.GREEN + 'Seasonal save Path: ' + colors.END +  str(config.seasonal_file_path))
    print(colors.GREEN + "Downloads are stored in: " + colors.END +
          str(config.download_folder_path))
    menu() 
    

