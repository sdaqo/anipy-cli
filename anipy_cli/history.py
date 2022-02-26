import json
import sys

from .misc import error
from . import config

class history():
    """
    Class for history. 
    Following entry fields are required 
    for writing to history file:
        - show_name
        - category_url
        - ep_url
        - ep
    """
    def __init__(self, entry) -> None:
       self.entry = entry
    
    def read_save_data(self):
        """
        Read history file, if
        it doesn't exist create it, 
        along with user_files folder.
        """
        while True:
            try:
                with config.history_file_path.open('r') as data:
                    self.json = json.load(data)
                break
            except FileNotFoundError:
                try:
                    config.user_files_path.mkdir(exist_ok=True)
                    config.history_file_path.touch(exist_ok=True)
                    # avoids error on empty json file
                    with config.history_file_path.open('a') as f:
                        f.write('{}')
                    continue
                except PermissionError:
                    error("Unable to create history file due to permissions.")
                    sys.exit()
        
        return self.json

    def check_duplicate(self):
        """
        Check if show is already in 
        history file.
        """
        for i in self.json:
            if i == self.entry.show_name:
                self.dup = True
                return 1
            else:
                pass

        self.dup = False

    def prepend_json(self):
        """Moves data to the top of a json file"""
        new_data = self.json[self.entry.show_name]
        self.json.pop(self.entry.show_name)
        new_data = {
            self.entry.show_name: (new_data)
        }  
        self.json = {**new_data, **self.json}
    
    def update_hist(self):
        self.json[self.entry.show_name]['ep'] = self.entry.ep
        self.json[self.entry.show_name]['ep-link'] = self.entry.ep_url       

    def write_hist(self):
        """
         Write json that looks something like this
         {"some-anime": 
                {
                 "ep": 1,
                 "ep-link": "https://ep-link", 
                 "category_url": "https://"
                 } 
          "another-anime": ...} 
        """

        self.read_save_data()
        self.check_duplicate()
        if self.dup:
            self.update_hist()
        else:
            add_data = { self.entry.show_name: {
                            "ep": self.entry.ep,
                            "ep-link": self.entry.ep_url,
                            "category-link": self.entry.category_url
                            }
                        }
            self.json.update(add_data)
        
        self.prepend_json()

        try:
            with config.history_file_path.open('w') as f:
                json.dump(self.json, f)
        except PermissionError:
                error("Unable to write to history file due permissions.")
                sys.exit()
