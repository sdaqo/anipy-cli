#### Linux:

First, run `make` to install the dependencies. After that, chose an installation method below. 

#### Normal Install

This is the default and recommended method. 

Pros:
- Works well with default config settings
- Will not need to reinstall to have changes in config or other code applied

Cons:
- Requires keeping and not moving this repo folder after install

To install via this method, run `sudo make install`.
If you would ever like to uninstall, run `sudo make uninstall`.

##### Persistent Install

This method does still work and will allow for viewing anime with ease via the commandline, however it is new and this project does not support it as well.

Pros:
- Allows this folder to deleted or moved after install if you do not want it

Cons:
- The default downloads path causes downloads to be in `/usr/local/lib/anipy-cli/downloads` 
- If the config.py file is edited from the cloned repo (this folder) you will need to reinstall it

To install via this method, run `sudo make sys-install`.
If you would ever like to uninstall, run `sudo make uninstall`.

#### Windows:

The windows installer is somewhat unstable so please open an issue when errors occur.

To install:
- Start a CMD session as administrator
- CD in the win folder of anipy-cli
- Type `win-installer.bat`
- It will now install python libs, create a bin folder in the root directory of anipy-cli that contains a anipy-cli.bat file and set a entry to the system path variable.
- You may have to reboot your PC before going to the next step.
- Now open a new cmd (if you want color support get windows terminal from microsoft store) and type `anipy-cli`

To uninstall:
- Start a CMD session as administrator
- CD in the win folder of anipy-cli
- Type `win-uninstaller.bat`
- It will now delete the bin folder, but it will NOT delete the entry to the path variable, you should delete that yourself.

