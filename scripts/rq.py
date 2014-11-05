import sys
import ast
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
	parser.add_argument('path', nargs='+',
		help='path components of the URL to access. If a path '
		'component contains a "=", then is interpreted as a variable '
		'with the format <key>=<val> which, depending on the verb '
		'used, will be sent as a query string parameter or as json in '
		'the body of the request. If <val> starts with a letter, it '
		'will be interpreted as a string, otherwise it is interpreted '
		'as a python literal. Normal path components will be joined '
		'using a "/" separator and properly escaped, so if you write '
		'"some/path", it will be escaped as "some%%2Fpath", you need '
		'to always provide path components separated by spaces '
		'(as different arguments)')
	args = parser.parse_args(args)
	path, opts = parse_args(args.path)
	verb = __name__ if __name__ in VERBS else args.verb
	res = rq.json_req(path, verb, **opts)
	print_obj(res)

def print_dict(d, prefix=u''):
	kwidth = max((len(k) for k in d))
	for k, v in d.items():
		print (prefix + u'%- ' + unicode(kwidth) + u's %s') % (k, v)

def print_obj(obj, prefix=u''):
	if isinstance(obj, dict):
		print_dict(obj, prefix)
	elif isinstance(obj, list):
		for i, d in enumerate(obj):
			print prefix + u'Item', i
			print_obj(d, prefix + u'\t')
			print
	elif obj:
		print prefix + obj

def parse_args(args):
	path = ''
	opts = dict()
	method = args[0].lower()
	for arg in args:
		if '=' in arg:
			key, val = arg.split('=', 1)
			if val[0].isalpha():
				opts[key] = val
			else:
				opts[key] = ast.literal_eval(val)
		else:
			path += '/' + urllib.quote_plus(arg)
	return path, opts

