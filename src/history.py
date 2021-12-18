import time
import os
from src import play

GREEN = '\033[92m'
ERROR = '\033[93m'
END = '\x1b[0m'


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
        # match exsisting with provided link so we can add the newly watched seconds, when link already in history, to the old ones
        if is_history == True: 
            
            time.sleep(10) #delay until player opens (guessed) 
            while play.stop == False:
                time.sleep(1)
                seconds += 1

            changed_line = data[index].split("#")
            changed_secs = changed_line[1].replace(changed_line[1], str(seconds + int(changed_line[1])))
            changed_line = changed_line[0] + "#" + changed_secs + "\n"
            data[index] = changed_line
            data += [data.pop(index)] #move element to last line
            f = open("history/history.txt", "w")
            for element in data:    
                f.write(element)
        else:
            # if already in history and the episode is played from history-selection, move it to firstt plavce in history 
            data += [data.pop(index)]
            f = open("history/history.txt", "w")
            for element in data:    
                f.write(element)
                
    else:
        # loop to measure time until player is closed
        time.sleep(10) #delay until player opens (guessed) 
        while play.stop == False:
            
            time.sleep(1)
            seconds += 1
            
        f = open("history/history.txt", "a")
        # seperate link and seconds with "#" to make it esier to read history
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


    except:
        pass
    
    return links, resume_seconds

def pick_history():
    
    #read history and reverse lists so last history-point is first in selection
    history = read_history()
    links = history[0]
    resume_seconds = history[1]
    links.reverse()
    resume_seconds.reverse()

    if not links:
        print(ERROR + "No history")
        quit()
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