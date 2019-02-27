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


from __future__ import division

import os
import sys
import time
import json
import errno
import argparse
import datetime
from zipfile import ZipFile, ZIP_DEFLATED
from urllib2 import HTTPError
try:
	import ttystatus
	if sys.stdout.isatty():
		status_base = ttystatus.TerminalStatus
	else:
		status_base = dict
except ImportError:
        sys.stderr.write("Warning: python-ttystatus package not present, not "
		"showing nice progress\n")
	status_base = dict

desc = 'backup a GitHub repository API metadata (issues, comments, etc.)'


def main(rq, args, config):
	prog = config.prog + ' ' + __name__
	parser = argparse.ArgumentParser(prog=prog, description=desc)
	parser.add_argument('what', nargs='+',
		help="organization, user or repository to backup (if the name "
		"contains a '/' is interpreted as a repository, if it doesn't, "
		"as a user or organization")
	parser.add_argument('-f', '--file-name', default='backup.zip',
		help="ZIP filename where to write the backup to (if not "
		"specified, a ZIP file is created per org / user / repository")
	parser.add_argument('-r', '--recursive', action='store_true',
		help="backup all the repositories for a user/organization")
	parser.add_argument('-i', '--incremental', action='store_true',
		help="adds files to the archive and only gets data that have"
		"changed since")
	parser.add_argument('-v', '--verbose', action='count', default=1,
		help="print more progress information")
	parser.add_argument('-q', '--quiet', action='count', default=0,
		help="don't print progress information")
	args = parser.parse_args(args)

	global verbose
	verbose = args.verbose - args.quiet

	global status
	status = Status()

	orgs, users, repos = parse_repos(rq, args.what, args.recursive)

	backup = Backup(rq, args)

	success = False
	try:
		status.format('%ElapsedTime() [Orgs(%Integer(odone)/%Integer(ototal))/'
				'Users(%Integer(udone)/%Integer(utotal))/'
				'Repos(%Integer(rdone)/%Integer(rtotal)) | '
				'Curr: %Pathname(curr)%Pathname(path) '
				'[%Integer(done)/%Integer(total), '
				'%PercentDone(done,total), '
				'ETA %RemainingTime(done,total)]')
		status['curr'] = '?'
		status['path'] = '/'
		status['total'] = len(orgs)+len(users)+len(repos)
		status['done'] = 0
		status['ototal'] = len(orgs)
		status['odone'] = 0
		status['utotal'] = len(users)
		status['udone'] = 0
		status['rtotal'] = len(repos)
		status['rdone'] = 0

		for org in orgs:
			status['curr'] = org
			status.flush()
			backup.backup_org(org)
			status['done'] += 1
			status['odone'] += 1

		for user in users:
			status['curr'] = user
			status.flush()
			backup.backup_user(user)
			status['done'] += 1
			status['udone'] += 1

		for repo in repos:
			status['curr'] = repo
			status.flush()
			backup.backup_repo(repo)
			status['done'] += 1
			status['rdone'] += 1
		success = True
	finally:
		status.finish()
		backup.newzipfile.close()
		if backup.zipfile is not None:
			backup.zipfile.close()
		if success:
			os.rename(backup.newzipfname, backup.zipfname)


def parse_repos(rq, stuff, recursive):
	orgs = set()
	users = set()
	repos = set()
	for s in stuff:
		if '/' in s:
			repos.add(s)
		else:
			users.add(s)
	if not users:
		return [], [], sorted(repos)

	status.format('%ElapsedTime() Inspecting users/orgs: %Pathname(owner) '
			'[%Integer(done)/%Integer(total), '
			'%PercentDone(done,total), '
			'ETA %RemainingTime(done,total)]')
	status['owner'] = '?'
	status['total'] = len(users)
	status['done'] = 0

	for u in sorted(users):
		status['owner'] = u
		status.flush()
		try:
			checked_rq(rq.get, '/orgs/%s/repos' % u)
			url = '/orgs/%s/repos' % u
			type = 'sources'
			users.remove(u)
			orgs.add(u)
		except HTTPError as e:
			if e.getcode() != 404:
				raise e
			url = '/users/%s/repos' % u
			type = 'owner'
		if recursive:
			rr = checked_rq(rq.get, url, type=type)
			repos.update(r['full_name'] for r in rr)
		status['done'] += 1

	status.clear()

	return sorted(orgs), sorted(users), sorted(repos)


class Backup:

	def __init__(self, rq, args):
		self.rq = rq
		self.args = args
		self.path = None
		self.zipfname = self.args.file_name
		self.newzipfname = self.zipfname + '.new'
		self.zipfile = None
		if args.incremental:
			try:
				self.zipfile = ZipFile(self.zipfname, 'r', allowZip64=True)
			except IOError as e:
				if e.errno != errno.ENOENT:
					raise e
		self.newzipfile = ZipFile(self.newzipfname, 'w', ZIP_DEFLATED, \
			allowZip64=True)

	def backup_org(self, org):
		self.path = org
		path = '/orgs/' + org
		self.write_url(path)
		path += '/'
		self.write_url(path + 'members')
		self.write_url(path + 'invitations')
		self.write_url(path + 'outside_collaborators')
		self.write_url(path + 'hooks')
		self.write_url(path + 'blocks',
				'application/vnd.github.giant-sentry-fist-preview+json')
		self.backup_projects(path + 'projects')
		self.backup_teams(path + 'teams')

	def backup_user(self, user):
		self.path = user
		path = '/users/' + user
		self.write_url(path)

	def backup_projects(self, path):
		local = False
		write_url = lambda path, **kwa: self.write_url(path,
			'application/vnd.github.inertia-preview+json', local,
			**kwa)
		try:
			projs, _ = write_url(path, state='all')
		except HTTPError as e:
			if e.getcode() == 410:
				status.verbose('Skipped disabled {}',
						self.zippath(path))
			else:
				raise e
		else:
			for proj in projs:
				write_url(proj['url'])
				columns, local = write_url(proj['columns_url'])
				for col in columns:
					write_url(col['cards_url'])

	def backup_teams(self, path):
		local = False
		write_url = lambda path: self.write_url(path,
			'application/vnd.github.hellcat-preview+json', local)
		teams, _ = write_url(path)
		for team in teams:
			team, local = write_url(team['url'])
			write_url(team['members_url'])
			write_url(team['repositories_url'])

	def backup_repo(self, repo):
		self.path = repo
		path = '/repos/' + repo
		self.write_url(path)
		path += '/'
		self.write_url(path + 'labels')
		self.write_url(path + 'milestones')
		self.write_url(path + 'comments')
		self.write_url(path + 'keys')
		self.write_url(path + 'deployments')
		self.write_url(path + 'hooks')
		self.write_url(path + 'releases')
		self.write_url(path + 'invitations')
		self.write_url(path + 'collaborators',
			'application/vnd.github.hellcat-preview+json')
		self.backup_projects(path + 'projects')
		self.backup_issues(path + 'issues')

	def backup_issues(self, path):
		local = False
		write_url = lambda path, **kwa: self.write_url(path,
			'application/vnd.github.squirrel-girl-preview', local,
			**kwa)
		issues, _ = write_url(path, state='all', sort='created',
				direction='asc')
		for issue in issues:
			local = False
			issue, local = write_url(issue['url'])
			write_url(issue['comments_url'])
			write_url(issue['events_url'])
			if 'pull_request' not in issue:
				continue
			local = False
			pr, local = write_url(issue['pull_request']['url'])
			write_url(pr['review_comments_url'])
			write_url(pr['commits_url'])
			write_url(pr['statuses_url'])
			self.write_url(issue['pull_request']['url'] +
				'/requested_reviewers',
				'application/vnd.github.thor-preview+json')
			reviews, _ = write_url(issue['pull_request']['url'] +
					'/reviews')
			for review in reviews:
				rev_path = '{}/reviews/{}'.format(
						issue['pull_request']['url'],
						review['id'])
				local = False
				review, local = write_url(rev_path)
				write_url(rev_path + '/comments')

	def write_url(self, path, accept=None, local=False, **kwargs):
		old_accept = self.rq.accept
		self.rq.accept = accept or old_accept
		import re
		path = re.sub(r'\{.+\}$', '', path)
		url = path
		if path.startswith(self.rq.base_url):
			path = path[len(self.rq.base_url):]
		status['path'] = path
		try:
			path = path.lstrip('/')
			obj = None
			etag = None
			if self.args.incremental:
				etag, obj = self.read(path)
			if obj is not None and local:
				self.write(path, obj, etag)
				status.verbose('Skipped unmodified {}',
						self.zippath(path))
				return obj, True
			if etag:
				self.rq.headers.append(('If-None-Match', etag))
			r = checked_rq(self.rq.get_full, url, **kwargs)
			if r is None: # ETag matched
				status.verbose("Skipped unmodified {}",
						self.zippath(path))
				self.write(path, obj, etag)
				return obj, True
			responses, obj = r
			# To make things simpler, we just save the ETag
			# of the first response (TODO: see if it works
			# in practice)
			self.write(path, obj, responses[0].headers.get('ETag'))
			if etag is None:
				status.info('Added {}', self.zippath(path))
			else:
				status.info('Updated {}', self.zippath(path))
			return obj, False
		finally:
			self.rq.accept = old_accept

	def read(self, path):
		if self.zipfile is None:
			return None, None
		path = self.zippath(path)
		try:
			data = json.loads(self.zipfile.read(path))
		except KeyError as e:
			return None, None
		return data['etag'], data['contents']

	def write(self, path, contents, etag=None):
		zip_path = self.zippath(path)
		data = dict(etag=etag, contents=contents)
		try:
			old_data = json.loads(self.newzipfile.read(zip_path))
		except KeyError as e:
			old_data = None
		if old_data is None:
			self.newzipfile.writestr(zip_path,
					json.dumps(data, indent=2))
		else:
			if data['etag'] != old_data['etag']:
				status.warn('{} already exist with '
					'a non-matching ETag (old: {}, '
					'new: {}), new value will be '
					'discarded',
					path, old_data['etag'], data['etag'])
			else:
				status.verbose('Skipping {}, already exist',
						path)

	def zippath(self, path):
		return self.path + '/' + (path + '.json').encode('utf-8')


def checked_rq(rq_fn, url, **kwargs):
	retries=10
	for i in range(retries):
		class fmtfloat(float):
			def __format__(self, fmt):
				if self > 1: fmt = '0'
				if not fmt: fmt = '3'
				return "{0:.{1}f}".format(float(self), fmt) \
						.rstrip('0').rstrip('.')
		# Exponential backoff (30ms - 16s) in case of errors
		wait_secs = fmtfloat(2**i / 2**(retries/2))
		try:
			r = rq_fn(url, **kwargs)
		except HTTPError as e:
			# Errors that are not transient and should be handled
			# by the caller
			if e.getcode() in (404, 410):
				raise e
			elif e.getcode() == 403: # Ratelimit
				remaining = int(e.headers.get(
					'X-RateLimit-Remaining'))
				if remaining != 0:
					raise e
				utc_ts = int(e.headers.get('X-RateLimit-Reset'))
				reset = datetime.datetime(
						*time.gmtime(int(utc_ts))[:6])
				wait = reset - datetime.datetime.now()
				wait_secs = wait.total_seconds()
				# Because of rounding and the time passed
				# between when we did the request and the
				# "now()", it could happen that we get a very
				# small negative wait
				if wait_secs < 0:
					continue
				status.warn("We just hit GitHub's rate-limit "
					"retrieving {}, waiting {:1}min "
					"(until {})...", url,
					fmtfloat(wait_secs / 60),
					reset.strftime('%c'))
				time.sleep(wait_secs)
				continue
			elif e.getcode() == 304: # ETag matches
				return None
			else:
				status.warn("HTTP error while retrieving {}: "
						"{}, retrying in {}s...",
						url, e, wait_secs)
				time.sleep(wait_secs)
				continue
		except IOError as e:
			status.warn("I/O error while retrieving {}: {}, "
					"retrying in {}s...",
					url, e, wait_secs)
			time.sleep(wait_secs)
			continue
		break
	else:
		sys.stderr.write("Too many retries, giving up!\n")
		sys.exit(10)
	return r


class Status(status_base):
	def __init__(self):
		self.is_dict = status_base is dict
		self.super = super(Status, self)
		if self.is_dict:
			self.super.__init__()
		else:
			self.super.__init__(period=0.1)

	def format(self, fmt):
		global verbose
		if self.is_dict or verbose == 0:
			return
		self.super.format(fmt)

	def warn(self, fmt, *args):
		global verbose
		if verbose < 0:
			return
		msg = 'Warning: ' + fmt.format(*args)
		if self.is_dict:
			sys.stderr.write(msg + '\n')
		else:
			self.super.notify(msg)

	def info(self, fmt, *args):
		global verbose
		if verbose < 1:
			return
		msg = fmt.format(*args)
		if self.is_dict:
			sys.stdout.write(msg + '\n')
		else:
			self.super.notify(msg)

	def verbose(self, fmt, *args):
		global verbose
		if verbose < 2:
			return
		msg = fmt.format(*args)
		if self.is_dict:
			sys.stdout.write(msg + '\n')
		else:
			self.super.notify(msg)

	def flush(self):
		if self.is_dict:
			sys.stdout.flush()
		else:
			self.super.flush()

	def finish(self):
		if self.is_dict:
			sys.stdout.flush()
		else:
			self.super.finish()

