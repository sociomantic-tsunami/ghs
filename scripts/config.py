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


import sys
import argparse

desc = 'get configuration values from ghs'

def main(rq, args, config):
	prog = config.prog + ' ' + __name__
	parser = argparse.ArgumentParser(prog=prog, description=desc)
	parser.add_argument('name', nargs='*',
		help="name of the variable to get")
	parser.add_argument('-l', '--list', metavar='WHAT', nargs='?',
		const='name', choices=['name', 'value', 'both'],
		help="list all variables in the config (WHAT: name, value "
		"or both; defaults to name)")
	args = parser.parse_args(args)

	if args.list and args.name:
		parser.error("Too many arguments for `--list`")

	if not args.list and not args.name:
		parser.error("Too too few arguments")

	if args.list:
		fmt = '{name}={value}' if args.list == 'both' \
				else '{' + args.list + '}'
		for name, value in ((n, getattr(config, n)) for n in dir(config)
				if not n.startswith('__')):
			print(fmt.format(name=name, value=value))
		return

	failed = False
	for name in args.name:
		try:
			print(getattr(config, name))
		except AttributeError as e:
			sys.stderr.write("Unknown config variable '{}'!\n"
					.format(name))
			failed = True

	if failed:
		sys.exit(1)

