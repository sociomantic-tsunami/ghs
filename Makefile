
prefix ?= /usr/local

export PYTHON := python

version ?= $(shell git describe --dirty 2> /dev/null | cut -b2-)
version := $(if $(version),$(version),devel)

.PHONY: default
default: all

.PHONY: all
all: man

.PHONY: deb
deb:
	$(MAKE) prefix=/usr DESTDIR=deb/install install
	deb/build

.PHONY: man
man: ghs.1

ghs.1: man.rst
	sed 's/^:Version: devel$$/:Version: $(version)/' $< | \
		rst2man --exit-status=1 > $@ || ($(RM) $@ && false)

.PHONY: install
install: ghs ghs.1 man.rst $(wildcard scripts/*.py)
	install -m 755 -D ghs $(DESTDIR)$(prefix)/bin/ghs
	sed -i 's/^VERSION = "ghs devel"$$/VERSION = "ghs $(version)"/' \
			$(DESTDIR)$(prefix)/bin/ghs
	sed -i 's|^#!/usr/bin/env python$$|#!/usr/bin/env $(PYTHON)|' \
			$(DESTDIR)$(prefix)/bin/ghs
	sed -i 's|^	script_dirs = \["~/\.ghscripts"\],$$|	script_dirs = ["~/.ghscripts", "$(prefix)/share/ghs/scripts"],|' \
			$(DESTDIR)$(prefix)/bin/ghs
	install -m 755 -d $(DESTDIR)$(prefix)/share/ghs/scripts
	install -m 644 -D -t $(DESTDIR)$(prefix)/share/ghs/scripts scripts/*.py
	install -m 644 -D ghs.1 $(DESTDIR)$(prefix)/share/man/man1/ghs.1
	install -m 644 -D man.rst $(DESTDIR)$(prefix)/share/doc/ghs/README.rst

.PHONY: release
release:
	@read -p "Enter version (previous: $$(git describe --abbrev=0)): " version; \
	test -z $$version && exit 1; \
	msg=`echo $$version | sed 's/v/Version /;s/-rc/ Release Candidate /'`; \
	echo ; \
	echo Changelog: ; \
	git log --format='* %s (%h)' `git describe --abbrev=0 HEAD^`..HEAD; \
	echo ; \
	set -x; \
	git tag -a -m "$$msg" $$version

.PHONY: clean
clean:
	$(RM) -r ghs.1 deb/*.deb deb/install

