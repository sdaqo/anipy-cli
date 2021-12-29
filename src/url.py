# local imports
from src.colors import colors
from src import history
# imports
import sys
import platform
import os
import requests
import re
import webbrowser
import time
from bs4 import BeautifulSoup
from selenium import webdriver
import subprocess

os.environ['WDM_LOG_LEVEL'] = '0'

headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36 Edg/95.0.1020.44"
}


def get_default_browser():

    if os.name in ('nt', 'dos'):
        from winreg import HKEY_CLASSES_ROOT, HKEY_CURRENT_USER, OpenKey, QueryValueEx

        with OpenKey(HKEY_CURRENT_USER, r'SOFTWARE\Microsoft\Windows\Shell\Associations\UrlAssociations\http\UserChoice') as regkey:
            browser_choice = QueryValueEx(regkey, 'ProgId')[0]

        with OpenKey(HKEY_CLASSES_ROOT, r'{}\shell\open\command'.format(browser_choice)) as regkey:
            browser_path_tuple = QueryValueEx(regkey, None)
            return browser_path_tuple[0].split('"')[1]
    elif platform.system() in ('Darwin'):
        """ needs implementation """
        return ""
    elif platform.system() in ('Linux'):
        program_name = "xdg-mime"
        arguments = ["query", "default"]
        last_argument = ["x-scheme-handler/https"]

        command = [program_name]
        command.extend(arguments)
        command.extend(last_argument)

        output = subprocess.Popen(
            command, stdout=subprocess.PIPE).communicate()[0]
        return output.decode('utf-8').splitlines()[0]
    else:
        return ""


def get_embed_url(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.content, "html.parser")
    link = soup.find("a", {"href": "#", "rel": "100"})
    return f'https:{link["data-video"]}'


def get_video_url(embed_url, link_with_episode, user_quality):
    print("Getting video url")
    try:
        try:
            """new code"""
            os.environ['MOZ_HEADLESS'] = '1'
            try:
                if "chrome" in get_default_browser():
                    from webdriver_manager.chrome import ChromeDriverManager

                    browser = webdriver.Chrome(
                        executable_path=ChromeDriverManager().install(), service_log_path=os.devnull)

                elif "chromium" in get_default_browser():
                    from webdriver_manager.chrome import ChromeDriverManager
                    from webdriver_manager.utils import ChromeType

                    browser = webdriver.Chrome(ChromeDriverManager(
                        chrome_type=ChromeType.CHROMIUM).install(), service_log_path=os.devnull)

                else:
                    print("Defaulting to firefox")
                    from webdriver_manager.firefox import GeckoDriverManager

                    browser = webdriver.Firefox(
                        executable_path=GeckoDriverManager().install(), service_log_path=os.devnull)

            except:
                print("Webdriver could not start, supported browsers are Firefox, Chrome and Chromium, please refer to https://github.com/sdaqo/anipy-cli/blob/master/README.md for install-instructions.")

            browser.get(embed_url)
            # start the player in browser so the video-url is generated

            browser.execute_script(
                'document.getElementsByClassName("jw-icon")[2].click()')
            html_source = browser.page_source
            soup = BeautifulSoup(html_source, "html.parser")
            # get quality options
            try:
                qualitys = soup.find(id="jw-settings-submenu-quality")
                user_quality = quality(qualitys, user_quality)
                # Click the quality, the user picked, in the quality selection, so the right link is being generated.
                browser.execute_script(
                    "document.evaluate('//*[@id=\"jw-settings-submenu-quality\"]/div/button[{0}]', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.click()".format(user_quality + 1))
            except:
                print(
                    "Something went wrong with the quality selection. Loading default quality.")
                time.sleep(1.5)
            # extract video link
            html_source = browser.page_source
            soup = BeautifulSoup(html_source, "html.parser")
            link = soup.find("video")
            link = link.get('src')
            browser.quit()
        except KeyboardInterrupt:
            print(colors.ERROR + "Interrupted" + colors.END)
            browser.quit()
            sys.exit()

        """old code"""
        # link = soup.find("video", {"class": "jw-video"})
        # print(f'https:{link["src"]}')
        # link = re.search(r"\s*sources.*", str(r.text)).group()
        # link = re.search(r"https:.*(m3u8)|(mp4)", link).group()
    except Exception as e:
        try:
            browser.quit()
        except:
            pass

        print(colors.ERROR + "[Exception] " + str(e) + colors.END +
              "\nIf you get this error a lot please feel free to open a Issue on github: https://github.com/sdaqo/anipy-cli/issues")
        open_in_browser = input(
            colors.ERROR + "Oops, an exception occured. Do you want to watch the Episode in the browser? (y/N): ")
        if open_in_browser == "y" or open_in_browser == "Y":
            webbrowser.open(embed_url)
            # False and True refer to is_history and is_on_web
            history.write_history(link_with_episode, False, True)
            print(colors.GREEN + "Episode saved in history" + colors.END)
            sys.exit()
        else:
            sys.exit()

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
                print(colors.ERROR + "Your quality is not avalible using: " +
                      qualitys[quality] + "p" + colors.END)
                time.sleep(1.5)
                pass

    except:

        pass

    return quality
