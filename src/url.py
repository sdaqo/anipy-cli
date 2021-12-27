import queue, os, requests, re, webbrowser, time, subprocess as sp
from bs4 import BeautifulSoup, NavigableString, Comment
from src.colors import colors
from main import history
from selenium import webdriver
from threading import Thread

headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36 Edg/95.0.1020.44"
    }


def get_embed_url(url):
    
    r = requests.get(url)
    soup = BeautifulSoup(r.content, "html.parser")
    link = soup.find("a", {"href": "#", "rel": "100"})
    return f'https:{link["data-video"]}'


def get_video_url(embed_url, link_with_episode, user_quality):
    print("Getting video url")
    try:
        """new code"""
        os.environ['MOZ_HEADLESS'] = '1'
        try:
            browser = webdriver.Firefox()
        except:
            print("Firefox geckodriver Webdriver is not instaled or not in PATH, please refer to https://github.com/sdaqo/anipy-cli/blob/master/README.md for install-instructions.")
        
        browser.get(embed_url)
        # start the player in browser so the video-url is generated 
        browser.execute_script('document.getElementsByClassName("jw-icon")[2].click()')
        html_source = browser.page_source
        soup = BeautifulSoup(html_source, "html.parser")
        # get quality options
        try:
            qualitys = soup.find(id="jw-settings-submenu-quality")
            user_quality = quality(qualitys, user_quality)
            # Click the quality, the user picked, in the quality selection, so the right link is being generated. 
            browser.execute_script("document.evaluate('//*[@id=\"jw-settings-submenu-quality\"]/div/button[{0}]', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.click()".format(user_quality + 1))
        except:
            print("Something went wrong with the quality selection. Loading default quality.")
            time.sleep(1.5)
        # extract video link
        html_source = browser.page_source
        soup = BeautifulSoup(html_source, "html.parser")
        link = soup.find("video")
        link = link.get('src')
        browser.quit()

        """old code"""
        #link = soup.find("video", {"class": "jw-video"})
        #print(f'https:{link["src"]}')
        #link = re.search(r"\s*sources.*", str(r.text)).group()
        #link = re.search(r"https:.*(m3u8)|(mp4)", link).group()
    except Exception as e:
        try:
            browser.quit()
        except:
            pass
        
        print(colors.ERROR + "[Exception] " + str(e) + colors.END + "\nIf you get this error a lot please feel free to open a Issue on github: https://github.com/sdaqo/anipy-cli/issues" )
        open_in_browser = input(colors.ERROR + "Oops, an exception occured. Do you want to watch the Episode in the browser? (y/N): ")
        if open_in_browser == "y" or open_in_browser == "Y":
            webbrowser.open(embed_url)
            history.write_history(link_with_episode, False, True) # False and True refer to is_history and is_on_web
            print(colors.GREEN + "Episode saved in history" + colors.END)
            quit()
        else:
            quit()
            
        
    return link

def quality(html_code, quality):

    
    if quality == None:
        quality = "best"
    else:
        pass

    try:

        qualitys = re.findall(r'\d+ P', str(html_code))

        temp_list = []
        for i in qualitys:
            if i not in temp_list:
                temp_list.append(i)
            else:
                pass  
        qualitys.clear()
        qualitys.extend(temp_list)

        for i in range(len(qualitys)):
            qualitys[i] = qualitys[i].replace(" P", "")

        if quality == "best" or quality == "worst":
            if quality == "best":
                quality = qualitys.index(qualitys[-1])
            else:
                quality = qualitys.index(qualitys[0])
        else:
            if quality in qualitys:
                quality = qualitys.index(quality)
            else:
                quality = qualitys.index(qualitys[-1])
                print(colors.ERROR + "Your quality is not avalible using: " + qualitys[quality] + "p" + colors.END)
                time.sleep(1.5)
                pass
            
    except:

        pass
    

    return quality
