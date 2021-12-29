PREFIX := /usr/local

all: dependencies install

dependencies:
	pip install -r requirements.txt
	cp $(CURDIR)/geckodriver $(PREFIX)/bin/
	chmod 0755 $(DESTDIR)$(PREFIX)/bin/geckodriver
install:
	echo "#!/bin/sh" > $(PREFIX)/bin/anipy-cli
	echo 'python $(CURDIR)/main.py $$1 $$2 $$3' >> $(PREFIX)/bin/anipy-cli
	chmod 0755 $(DESTDIR)$(PREFIX)/bin/anipy-cli

uninstall:
	$(RM) $(DESTDIR)$(PREFIX)/bin/anipy-cli

.PHONY: all dependencies install uninstall
