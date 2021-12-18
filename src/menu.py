# from src import play



GREEN = '\033[92m'
ERROR = '\033[93m'
END = '\x1b[0m'


def main_menu():
    options =[GREEN + "[n] " + END + "Next Episode", GREEN + "[p] " + END + "Previous Episode",
              GREEN + "[h] " + END + "History selection", GREEN + "[a] " + END + "Search for Anime",
              GREEN + "[q] " + END + "Quit"]
    
    
    for i in options:
        print(i)


main_menu()