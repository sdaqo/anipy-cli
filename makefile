PREFIX := /usr/local

all: dependencies install

dependencies:
	pip install -r requirements.txt
	cp $(CURDIR)/geckodriver $(PREFIX)/bin/

install:
	echo "#!/bin/sh" > $(PREFIX)/bin/anipy-cli
	echo python $(CURDIR)/main.py >> $(PREFIX)/bin/anipy-cli
	chmod 0755 $(DESTDIR)$(PREFIX)/bin/anipy-cli

uninstall:
	$(RM) $(DESTDIR)$(PREFIX)/bin/anipy-cli
	$(RM) $(DESTDIR)$(PREFIX)/bin/geckodriver

.PHONY: all dependencies install uninstall
