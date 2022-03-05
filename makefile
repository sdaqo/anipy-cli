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
	ln -s "$(CURDIR)/anipy_cli/run_anipy_cli.py" "$(PREFIX)/bin/anipy-cli"
	# Make sure that anipy-cli.py is executable
	chmod +x "$(CURDIR)/anipy_cli/run_anipy_cli.py"

sys-install:
	# This method does not require the user to keep this git repo folder
	mkdir -p "$(PREFIX)/lib"
	mkdir -p "$(PREFIX)/bin"

	# Delete the anipy-cli in bin folder so that 
	# the symlink can be made. It would fail if the 
	# old shell script was still there.
	$(RM) $(PREFIX)/bin/anipy-cli
	# Make a symlink to anipy-cli that is on the path
	ln -s "$(PREFIX)/lib/anipy_cli/run_anipy_cli.py" "$(PREFIX)/bin/anipy-cli"

	# Now install the program to lib
	cp -r "$(CURDIR)/anipy_cli" "$(PREFIX)/lib"

	# Make it writable, so that the current default config works	
	chmod -R 777 $(PREFIX)/lib/anipy_cli

lib-install:
	# This uses pip to install anipy-cli as a library
	python3 setup.py bdist_wheel
	pip3 install dist/anipy_cli-2.1.0-py3-none-any.whl

clean:
	# This gets rid of files generated from building via lib-install
	$(RM) -r build
	$(RM) -r dist
	$(RM) -r anipy_cli.egg-info

uninstall:
	# Get rid of the symlink
	$(RM) "$(PREFIX)/bin/anipy-cli"
	
	# Get rid of program data from older sys-install
	$(RM) "$(PREFIX)/lib/anipy-cli.py"
	$(RM) -r "$(PREFIX)/lib/anipy-cli"

	# Get rid of program data from the newer sys-install 
	$(RM) -r "$(PREFIX)/lib/anipy_cli"

all: dependencies install

.PHONY: all dependencies install sys-install uninstall lib-install clean
