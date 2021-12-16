import time
import os
from threading import Thread
import subprocess as sp


player = "mpv"
GREEN = '\033[92m'
ERROR = '\033[93m'
END = '\x1b[0m'


def play(embed_url, video_url, link, is_history, start_at="0"):
    global stop 
    stop = False
    player_command = player + " --start=+" + str(start_at) + " --cache=yes " +  '--http-header-fields="Referer: ' + embed_url + '"' + " " + video_url
    Thread(target=write_history, args=(link, is_history)).start()
    sp.run(player_command)
    stop = True

def write_history(link, is_history):

    # try making files and dirs    
    try:
        os.mkdir("history")
    except:
        pass
    
    try:
        open("history/history.txt", "x")
    except:
        pass
    
    # match exsisting with provided link  so we can change the newliy watched seconds when link already in jistory with the old ones
    f = open("history/history.txt", "rt")
    
    data = f.readlines()
    index = 0
    in_data = False
    seconds = 0
    
    
    for i in data:
        if link in i:
                index = index
                in_data = True
                break
        else:
            pass
        index += 1
    
    if in_data == True:
        if is_history == True:
            time.sleep(10) #delay until player opens (guessed) 
            while stop == False:
                time.sleep(1)
                seconds += 1

            changed_line = data[index].split("#")
            changed_secs = changed_line[1].replace(changed_line[1], str(seconds + int(changed_line[1])))
            changed_line = changed_line[0] + "#" + changed_secs + "\n"
            data[index] = changed_line
            f = open("history/history.txt", "w")
            for element in data:    
                f.write(element)
        else:
            pass
    else:
        time.sleep(10) #delay until player opens (guessed) 
        while stop == False:
            time.sleep(1)
            seconds += 1
            
        f = open("history/history.txt", "a")
        f.write(link + "#" + str(seconds) + "\n")

    
def read_history():
    try:
        f = open("history/history.txt", "rt")
        data = f.readlines()
        links = []
        resume_seconds = []
        
        
        for i in data:
            i = i.split("#")
            links.append(i[0])
            resume_seconds.append(i[1].replace("\n", ""))


    except Exception as a:
        print(a)
        pass
    
    return links, resume_seconds

def pick_history():
    
    #read history and reverse lists so last history-point is first in selection
    history = read_history()
    links = history[0]
    resume_seconds = history[1]
    links.reverse()
    resume_seconds.reverse()

    
    counter = 1
    for i in links:
        print(GREEN + "["+  str(counter) + "]" +  END + " " + str(i.replace("https://gogoanime.wiki/", "")))
        counter += 1
    
    which_anime = input("Enter Number: ")
    
    try: 
        link = links[int(which_anime) - 1]
        resume_seconds = resume_seconds[int(which_anime) - 1]
    except:
        print(ERROR + "Invalid Input")
        quit()
    
    return link, resume_seconds 
