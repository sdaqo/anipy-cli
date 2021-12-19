import requests, re, webbrowser, time, subprocess as sp
from bs4 import BeautifulSoup
from src.colors import colors


headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36 Edg/95.0.1020.44"
    }

def get_embed_url(url):
    
    r = requests.get(url)
    soup = BeautifulSoup(r.content, "html.parser")
    link = soup.find("a", {"href": "#", "rel": "100"})
    return f'https:{link["data-video"]}'


def get_video_url(embed_url):

    r = requests.get(embed_url, headers=headers)
    
    try:
        link = re.search(r"\s*sources.*", str(r.text)).group()
        link = re.search(r"https:.*(m3u8)|(mp4)", link).group()
    except:
        open_in_browser = input(colors.ERROR + "Oops, could not find video-url. Do you want to watch the Episode in the browser? (y/N): ")
        if open_in_browser == "y" or open_in_browser == "Y":
            webbrowser.open(embed_url)
            quit()
        else:
            quit()
            
        
    return link

def quality(video_url, embed_url, quality):

    # Using cUrl here because I just couldnt find a soulution 
    # for getting the quality-subprofiles of the m3u8-playlist
    # with request and bs4. 
    
    
    if quality == None:
        quality = "best"
    else:
        pass
    
    # skip if curl is not avalible, since the url also works without a specified quality
    try:
        cURL = 'curl -s --referer "{0}" "{1}"'.format(embed_url, video_url)

        response = sp.check_output(cURL,
                                   shell=True, 
                                   stderr=sp.DEVNULL)
        
        qualitys = re.findall(r'\d+p', response.decode('utf-8')) 
        for i in range(len(qualitys)):
            qualitys[i] = qualitys[i].replace("p", "")

        if quality == "best" or quality == "worst":
            if quality == "best":
                quality = qualitys[-1]
            else:
                quality = qualitys[0]
        else:
            if quality in qualitys:
                quality = quality
            else:
                quality = qualitys[-1]
                print(colors.ERROR + "Your quality is not avalible using: " + qualitys[-1] + "p" + colors.END)
                time.sleep(1.5)
                pass
            
        try:
            quality = quality.replace("p", "")
        except:
            pass
        
        url = video_url.replace("m3u8", "") + quality + ".m3u8"
        
    except:
        url = video_url
    
    return url