import sys
import ast
import json
import urllib
import argparse

VERBS = frozenset('head get post patch put delete'.split())

if __name__ in VERBS:
	desc = 'send a `' + __name__ + '` request to GitHub'
else:
	desc = 'send a request to GitHub'

def main(rq, args, config):
	prog = config.prog + ' ' + __name__
	parser = argparse.ArgumentParser(prog=prog, description=desc)
	if __name__ not in VERBS:
		parser.add_argument('verb', choices=VERBS,
			help='HTTP verb to use to send the query')
	parser.add_argument('--format', '-f',
		help='format to use to print each result for a response. '
		'Any field can be used from the response, json responses are '
		'converted to Python lists/dictionaries and the standard '
		'Python format() function is used for formatting. If the '
		'response is a list, then the format string is applied to the '
		'elements, the first argument ({0}) is the list index, and '
		'the object attributes are passed as key=value items, so you '
		'can reference them as {key} (same for one-object responses). '
		'For more details see: '
		'https://docs.python.org/3/library/string.html#formatstrings. '
		'By default the complete json response is printed')
	parser.add_argument('path', nargs='+',
		help='path components of the URL to access. If a path '
		'component contains a "=", then is interpreted as a variable '
		'with the format <key>=<val> which, depending on the verb '
		'used, will be sent as a query string parameter or as json in '
		'the body of the request. If <val> starts with a letter, it '
		'will be interpreted as a string (except for true/false, case '
		'insensitive), otherwise it is interpreted as a python '
		'literal. Normal path components will be joined using a "/" '
		'separator and properly escaped, so if you write "some/path", '
		'it will be escaped as "some%%2Fpath", you need to always '
		'provide path components separated by spaces (as different '
		'arguments)')
	args = parser.parse_args(args)
	path, opts = parse_args(args.path)
	verb = __name__ if __name__ in VERBS else args.verb
	res = rq.json_req(path, verb, **opts)
	if args.format is None:
		print(json.dumps(res, indent=4))
	else:
		if isinstance(res, list):
			for k, v in enumerate(res):
				print(args.format.format(k, **v))
		else:
			print(args.format.format(**res))

def parse_args(args):
	path = ''
	opts = dict()
	method = args[0].lower()
	for arg in args:
		if '=' in arg:
			key, val = arg.split('=', 1)
			if val.lower() in ('true', 'false'):
				opts[key] = True if val.lower() == 'true' \
						else False
			elif len(val) == 0 or val[0].isalpha():
				opts[key] = val
			else:
				opts[key] = ast.literal_eval(val)
		else:
			path += '/' + urllib.quote_plus(arg)
	return path, opts

