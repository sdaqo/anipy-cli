from src import play, query, url, history #local imports
import main
from src.colors import colors
import re, os, time, signal
from threading import Thread


options =[colors.GREEN + "[n] " + colors.END + "Next Episode", colors.GREEN + "[p] " + colors.END + "Previous Episode",
          colors.GREEN + "[r] " + colors.END + "Replay episode", colors.GREEN + "[h] " + colors.END + "History selection",
          colors.GREEN + "[a] " + colors.END + "Search for Anime", colors.GREEN + "[q] " + colors.END + "Quit"]

def clear_console():
    os.system('cls' if os.name=='nt' else 'clear')


def kill_subprocess():
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
    clear_console()
    print(colors.GREEN + "Playing: " + colors.RED + link.replace("https://gogoanime.wiki/", ""))
    
    for i in options:
        print(i) 
    
    while True:   
        which_option = input("Enter option: " + colors.CYAN)
        
        if which_option == "n": # next episode
            kill_subprocess()
            episode = re.search(r"[0-9]", link)
            episode = episode.group(0)
            link = link.replace(episode, str(int(episode) + 1))
            start_episode(link)
            main_menu(link)   
            
        elif which_option == "p": #previous episode
            
            episode = re.search(r"[0-9]", link)
            episode = episode.group(0)

            if episode == "1":
                print(colors.ERROR + "There is no episode before that.")
                pass
            else:
                kill_subprocess()
                link = link.replace(episode, str(int(episode) - 1))
                start_episode(link)
                main_menu(link)
                
        elif which_option == "r": # replay episode
            kill_subprocess()
            start_episode(link)
            main_menu(link)   
            
        elif which_option == "h": # History selection
            kill_subprocess() 
            clear_console()
            picked_history = history.pick_history()
            link_with_episode = picked_history[0]
            is_history = True
            start_episode(link_with_episode, picked_history[1], is_history)
            main_menu(link_with_episode)

        elif which_option == "a": # Anime Search
            kill_subprocess()
            clear_console()
            search = input("Search for Anime: " + colors.CYAN)
            print(colors.END)
            search_link = query.query(search)
            search_link_with_episode = query.episode(search_link)
            start_episode(search_link_with_episode)
            main_menu(search_link_with_episode)

        elif which_option == "q": # quit
            kill_subprocess()
            time.sleep(1.2) # wait until write_history is finished 
            quit()
            
        else:
            print(colors.ERROR + "Invalid Input" + colors.END)



def start_episode(link, resume_seconds = 0, is_history = False): 
         
    embed_url = url.get_embed_url(link)
    video_url = url.get_video_url(embed_url, link)    
    video_url = url.quality(video_url, embed_url, main.args.quality)
    
    if is_history == False:
        t1 = Thread(target=play.play , args=(embed_url, video_url, link, main.args.history,))
        t1.start()
    else:
        t1 = Thread(target=play.play , args=(embed_url, video_url, link, main.args.history, resume_seconds, ))
        t1.start()