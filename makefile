PREFIX := /usr/local

dependencies:
	pip3 install -r requirements.txt

install: 
	# Just makes the scipt accessable from the path
	
	# Delete the anipy-cli in bin folder so that 
	# the symlink can be made. It would fail if the 
	# old shell script was still there.
	$(RM) $(PREFIX)/bin/anipy-cli
	# Make a symlink to anipy-cli that is on the path
	ln -s "anipy-cli.py" "$(PREFIX)/bin/anipy-cli"
	# Make sure that anipy-cli.py is executable
	chmod +x "anipy-cli.py"

sys-install:
	# This method does not require the user to keep this git repo folder
	mkdir -p "$(PREFIX)/lib"
	mkdir -p "$(PREFIX)/bin"

	# Delete the anipy-cli in bin folder so that 
	# the symlink can be made. It would fail if the 
	# old shell script was still there.
	$(RM) $(PREFIX)/bin/anipy-cli
	# Make a symlink to anipy-cli that is on the path
	ln -s "$(PREFIX)/lib/anipy-cli.py" "$(PREFIX)/bin/anipy-cli"

	# Now install the program to lib
	cp -r anipy_cli "$(PREFIX)/lib"
	cp anipy-cli.py "$(PREFIX)/lib"
	chmod 775 "$(PREFIX)/lib/anipy-cli.py"

uninstall:
	# Get rid of the symlink
	$(RM) "$(PREFIX)/bin/anipy-cli"
	# Get rid of program data
	$(RM) "$(PREFIX)/lib/anipy-cli.py"
	$(RM) -r "$(PREFIX)/lib/anipy_cli"

all: dependencies install

.PHONY: all dependencies install sys-install uninstall
