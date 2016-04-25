import sys
import json
import argparse
from zipfile import ZipFile
from urllib2 import HTTPError
try:
	import ttystatus
	status = ttystatus.TerminalStatus(period=0.1)
except ImportError:
        sys.stderr.write("Warning: python-ttystatus package not present, not "
		"showing nice progress\n")
	status = dict()

desc = 'backup a GitHub repository API metadata (issues, comments, etc.)'

verbose = False

def main(rq, args, config):
	prog = config.prog + ' ' + __name__
	parser = argparse.ArgumentParser(prog=prog, description=desc)
	parser.add_argument('what', nargs='+',
		help="username or repository to backup (if the name contains "
		"a '/' is interpreted as a repository, if it doesn't, as a "
		"username/organization")
	parser.add_argument('-f', '--file-name',
		help="ZIP filename where to write the backup to (if not "
		"specified, a ZIP file is created per repository")
	parser.add_argument('-v', '--verbose', action='store_true',
		help="Print extra progress information")
	args = parser.parse_args(args)

	repos = parse_repos(rq, args.what)

	if args.verbose:
		global verbose
		verbose = True

	backup = Backup(rq, args)

	status_repos(repos)
	for repo in repos:
		status['repo'] = repo
		backup.backup(repo)
		status['repos_done'] += 1
	status_finish()


def parse_repos(rq, stuff):
	usernames = []
	repos = []
	for s in stuff:
		if '/' in s:
			repos.append(s)
		else:
			usernames.append(s)
	if not usernames:
		return repos

	status_usernames(usernames)
	for u in usernames:
		status['username'] = u
		try:
			rq.get('/orgs/' + u)
			url = '/orgs/%s/repos' % u
		except HTTPError as e:
			if e.getcode() != 404:
				raise e
			url = '/users/%s/repos' % u
		repos.extend(r['full_name'] for r in rq.get(url))
		status['usernames_done'] += 1

	return repos


class Backup:

	def __init__(self, rq, args):
		self.rq = rq
		self.args = args
		self.zipfile = None
		self.zipfname = None
		self.repo = None
		self.path = None

	def backup(self, repo):
		self.repo = repo
		self.path = repo
		self.zipfname = self.args.file_name
		if not self.zipfname:
			self.zipfname = self.path.replace('/', '_')  + '.zip'
		self.zipfile = ZipFile(self.zipfname, 'w')

		with self.zipfile:
			self.write_url('labels')
			self.write_url('milestones')
			self.write_url('comments')
			self.write_url('keys')
			self.write_url('hooks')
			self.write_url('releases')
			issues = self.rq.get('/repos/%s/issues' % repo,
				state='all', sort='created', direction='asc')
			status_reset_issues(issues)
			for issue in issues:
				status['issue'] = issue['number']
				self.backup_issue(issue)
				status['issues_done'] += 1
			status_reset_issues()

	def backup_issue(self, issue):
		self.write_issue_attr(issue, 'issue', 'url')
		self.write_issue_attr(issue, 'comments')
		self.write_issue_attr(issue, 'events')
		if 'pull_request' in issue:
			url = '/repos/%s/pulls/%s' % (self.repo, issue['number'])
			pr = self.rq.get(url)
			self.write_issue_attr(pr, 'review_comments')
			self.write_issue_attr(pr, 'commits')
			self.write_issue_attr(pr, 'statuses')

	def write_issue_attr(self, issue, name, url_key=None):
		path = 'issues/%s/%s' % (issue['number'], name)
		if url_key is None:
			url_key = name + '_url'
		self.write_url(path, issue[url_key])

	def write_url(self, name, url=None):
		if url is None:
			url = '/repos/%s/%s' % (self.repo, name)
		try:
			obj = self.rq.get(url)
			if obj:
				self.write(name, obj)
		except HTTPError as e:
			if e.getcode() != 404:
				raise e

	def write(self, name, obj):
		path = self.path + '/' + (name + '.json').encode('utf-8')
		status['path'] = path
		status_notify('{}: Adding {}', self.zipfname, path)
		self.zipfile.writestr(path, json.dumps(obj, indent=2))


def status_notify(fmt, *args):
	if not verbose:
		return

	msg = fmt.format(*args)
	if isinstance(status, dict):
		sys.stdout.write(msg + '\n')
	else:
		status.notify(msg)

def status_reset(repos=(), usernames=()):
	status['username'] = usernames[0] if usernames else '?'
	status['usernames'] = usernames
	status['usernames_done'] = 0
	status['usernames_total'] = len(usernames)

	status['repo'] = repos[0] if repos else '?'
	status['repos'] = repos
	status['repos_done'] = 0
	status['repos_total'] = len(repos)

	status_reset_issues()

def status_reset_issues(issues=()):
	status['issue'] = 0
	status['issues'] = [i['number'] for i in issues]
	status['issues_done'] = 0
	status['issues_total'] = len(issues)
	status['issue_part'] = ''

def status_repos(repos):
	if not isinstance(status, dict):
		status.clear()
	status_reset(repos)
	if isinstance(status, dict):
		return
	status.add(ttystatus.ElapsedTime())
	status.add(ttystatus.Literal(' Repo: '))
	status.add(ttystatus.Pathname('repo'))
	status.add(ttystatus.Literal(' ['))
	status.add(ttystatus.Index('repo', 'repos'))
	status.add(ttystatus.Literal(', '))
	status.add(ttystatus.PercentDone('repos_done', 'repos_total'))
	status.add(ttystatus.Literal(' done]'))
	status.add(ttystatus.Literal(' | Issue #'))
	status.add(ttystatus.String('issue'))
	status.add(ttystatus.Literal(' ('))
	status.add(ttystatus.Index('issue', 'issues'))
	status.add(ttystatus.Literal(', '))
	status.add(ttystatus.PercentDone('issues_done', 'issues_total'))
	status.add(ttystatus.Literal(' done, ETA '))
	status.add(ttystatus.RemainingTime('issues_done', 'issues_total'))
	status.add(ttystatus.Literal('): '))
	status.add(ttystatus.Pathname('path'))

def status_usernames(usernames):
	if not isinstance(status, dict):
		status.clear()
	status_reset([], usernames)
	if isinstance(status, dict):
		return
	status.add(ttystatus.ElapsedTime())
	status.add(ttystatus.Literal(' Username: '))
	status.add(ttystatus.Pathname('username'))
	status.add(ttystatus.Literal(' ['))
	status.add(ttystatus.Index('username', 'usernames'))
	status.add(ttystatus.Literal(', '))
	status.add(ttystatus.PercentDone('usernames_done', 'usernames_total'))
	status.add(ttystatus.Literal(' done, ETA '))
	status.add(ttystatus.RemainingTime('usernames_done', 'usernames_total'))
	status.add(ttystatus.Literal(']'))

def status_finish():
	if isinstance(status, dict):
		return
	status.finish()

