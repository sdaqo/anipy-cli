import time
import sys
import json
import requests
from urllib.parse import urlsplit, parse_qs
from requests import Request
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import re
import os
from bs4 import BeautifulSoup
import subprocess as sp

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
           
           if len(which_episode) == 1:
                try:
                    if int(which_episode[0])in list(range(1, self.entry.latest_ep + 1)):
                        return which_episode
                except:
                    error('invalid input')
           elif len(which_episode) == 2:     
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
           else:
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
        self.session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        self.ajax_url = "https://gogoplay.io/encrypt-ajax.php"
        self.key = '3235373436353338353932393338333936373634363632383739383333323838'
        self.iv = '34323036393133333738303038313335'
    
    def get_entry(self):
        """
        Returns the entry with stream and emebed url fields filled
        which was previously passed to this class.
        """
        return self.entry

    def embed_url(self):    
        r = self.session.get(self.entry.ep_url)
        response_err(r, self.entry.ep_url)
        soup = BeautifulSoup(r.content, "html.parser")
        link = soup.find("a", {"href": "#", "rel": "100"})
        loc_err(link, self.entry.ep_url, "embed-url")
        self.entry.embed_url = f'https:{link["data-video"]}'
    
    def decrypt_link(self):    
        splt_url = urlsplit(self.entry.embed_url)
        video_id = parse_qs(splt_url.query)['id'][0]
        # no permanent solution, I was just lazy
        cmd = f'printf \"{video_id}\" | openssl enc -aes-256-cbc -nosalt -e -K \"{self.key}\" -iv \"{self.iv}\" -a'
        return sp.getoutput(cmd)
        # return json
        
        # the code where I gave up, leaving this here for the future

        #BLOCK_SIZE = 16
        #pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * chr(BLOCK_SIZE - len(s) % BLOCK_SIZE)
        #
        #private_key = hashlib.sha256(self.key.encode("utf-8")).digest()
        #iv = binascii.unhexlify(self.iv) 
        #video_id = pad(video_id).encode('utf-8')
        #cipher = AES.new(private_key, AES.MODE_CBC, iv)
        #print(base64.b64encode(cipher.encrypt(video_id)))
        #ajax = base64.b64encode(iv + cipher.encrypt(video_id))

    def stream_url(self):
        """ 
        Fetches stream url and executes
        quality function.
        """
        if not self.entry.embed_url:
            self.embed_url()
        
        ajax = self.decrypt_link()
        headers = {'x-requested-with': 'XMLHttpRequest'}
        data = {'id': ajax, 'time': '69420691337800813569'}
        r = self.session.post(self.ajax_url, headers=headers, data=data)
        response_err(r, self.entry.embed_url)
        r = r.text.replace('\\', '')
        json_resp = json.loads(r)
        source_data = [x for x in json_resp['source']]
        self.quality(source_data)

    def quality(self, json_data):
        """
        Get quality options from
        m3u8 playlist, and change
        the m3u8 url to quality.
        """
        print(json_data)
        qualitys = []
        quality_links = []
        for i in json_data: 
            if i['label'] == 'Auto':
                pass
            else:
                qualitys.append(i['label'])
                quality_links.append(i['file'])
        
        qualitys = [x.replace(' P', '') for x in qualitys]

        if self.qual in qualitys:
            q = quality_links[qualitys.index(self.qual)]
        elif self.qual == 'best' or self.qual == None:
            q = quality_links[-1]
        elif self.qual == 'worst':
            q = quality_links[0]
        else:
            error("quality not avalible, using default")
            q = quality_links[-1]
        
        self.entry.stream_url = q
        print(q)
