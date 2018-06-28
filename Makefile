# This file is part of ghs.
#
# ghs is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ghs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ghs.  If not, see <https://www.gnu.org/licenses/>.
#
# Copyright (c) 2016-2018 dunnhumby Germany GmbH.
# All rights reserved.

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

