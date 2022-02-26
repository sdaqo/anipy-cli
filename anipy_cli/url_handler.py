import sys
import requests
import re
from bs4 import BeautifulSoup

from .misc import response_err, error, loc_err
from .colors import colors

class epHandler():
   """
   Class for handling episodes and stuff.
   Requires at least the category_url field of the
   entry to be filled.
   """
   def __init__(self, entry) -> None:
        self.entry = entry
    
   def get_entry(self):
        """
        Returns the entry with which was
        previously passed to this class.
        """
        return self.entry
   
   def get_latest(self):
        """ 
        Fetch latest episode avalible
        from a show and return it.
        """
        r = requests.get(self.entry.category_url)
        response_err(r, self.entry.category_url)
        soup = BeautifulSoup(r.content, "html.parser")
        ep_count = [
            i.get('ep_end') 
            for i in soup.find_all('a', attrs={'ep_end': re.compile(r"^ *\d[\d ]*$")})
        ]

        if not ep_count:
            error("could not get latest episode")
            sys.exit()      

        self.entry.latest_ep = int(ep_count[-1])
        
        return self.entry.latest_ep

   def pick_ep(self):
       """
       Cli function to pick a episode from 1 to
       the latest avalible.
       """
       if self.entry.latest_ep == 0:
           self.get_latest()
        
       while True:
           which_episode = input(colors.END + "Episode " + colors.GREEN + f"[1-{self.entry.latest_ep}]" 
                                 + colors.END + ": " +
                                 colors.CYAN)
           try:
               if int(which_episode) in list(range(1, self.entry.latest_ep + 1)):
                   self.entry.ep = int(which_episode)
                   self.gen_eplink() 
                   break
               else:
                   error("Number out of range.")

           except:  
               error("Invalid Input")
       
       return self.entry

   def pick_range(self):
       """ 
       Accept a range of episodes
       and return it. 
       Input/output would be 
       something like this:
            3-5 -> [3, 4, 5]
            3 -> [3]
       """
       self.entry.latest_ep = self.get_latest()
       while True:
           which_episode = input(colors.END 
                                 + "Episode " + colors.GREEN + f"[1-{self.entry.latest_ep}]" 
                                 + colors.END 
                                 + ": " +
                                 colors.CYAN)
            
           which_episode = which_episode.split('-')
           
           match len(which_episode):
                case 1:
                    try:
                        if int(which_episode[0])in list(range(1, self.entry.latest_ep + 1)):
                            return which_episode
                    except:
                        error('invalid input')
                case 2:
                    
                    try: 
                        ep_list = list(range(int(which_episode[0]), int(which_episode[1]) + 1))
                        if not ep_list:
                            error('invlid input')
                        else:
                            if ep_list[-1] > self.entry.latest_ep:
                                error('invalid input')
                            else:
                                return ep_list
                    except:
                        error('invalid input')
                case _:
                    error('invalid input')

     
   def gen_eplink(self):
        """ 
        Generate episode url
        from ep and category url
        will look something like this:
        https://gogoanime.film/category/hyouka
        to
        https://gogoanime.film/hyouka-episode-1 
        """
        self.entry.ep_url = self.entry.category_url.replace('/category', '')
        self.entry.ep_url = self.entry.ep_url + f'-episode-{self.entry.ep}'
        
        return self.entry        

class videourl():
    """ 
    Class that fetches embed and
    stream url. 
    """
    def __init__(self, entry, quality) -> None:
       self.entry = entry 
       self.qual = quality
    
    def get_entry(self):
        """
        Returns the entry with stream and emebed url fields filled
        which was previously passed to this class.
        """
        return self.entry

    def embed_url(self):    
        r = requests.get(self.entry.ep_url)
        response_err(r, self.entry.ep_url)
        soup = BeautifulSoup(r.content, "html.parser")
        link = soup.find("a", {"href": "#", "rel": "100"})
        loc_err(link, self.entry.ep_url, "embed-url")
        self.entry.embed_url = f'https:{link["data-video"]}'
    
    def stream_url(self):
        """ 
        Fetches stream url and executes
        quality function.
        For now some shows's stream url is  not able
        to be fetched because they are played
        from the streamsb server (e.g. sangatsu no lion)
        which has dirty javascript to avoid scraping.
        """
        if not self.entry.embed_url:
            self.embed_url()
            
        r = requests.get(self.entry.embed_url)
        response_err(r, self.entry.embed_url)
        self.entry.stream_url = re.search(r"(?<=file:\s\')https:.*(m3u8)|(mp4)", r.text)
        loc_err(self.entry.stream_url, self.entry.embed_url, 'stream-url')
        self.entry.stream_url = self.entry.stream_url.group()
        self.quality()

    def quality(self):
        """
        Get quality options from
        m3u8 playlist, and change
        the m3u8 url to quality.
        """
        r = requests.get(self.entry.stream_url, headers={"referer": self.entry.embed_url })
        response_err(r, self.entry.stream_url) 
        qualitys = re.findall(r'(?<=NAME=")(.+?(?=p))', r.text)
        
        if self.qual in qualitys:
            q = qualitys[qualitys.index(self.qual)]
        elif self.qual == 'best' or self.qual == None:
            q = qualitys[-1]
        elif self.qual == 'worst':
            q = qualitys[0]
        else:
            error("quality not avalible, using default")
            return None
        
        self.entry.stream_url = self.entry.stream_url.replace('m3u8', f'{q}.m3u8') 