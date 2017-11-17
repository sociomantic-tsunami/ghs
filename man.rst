
===
ghs
===

--------------
GitHub Scripts
--------------

:Author: Leandro Lucarella <leandro.lucarella@sociomantic.com>
:Copyright: 2014 Sociomantic Labs GmbH
:Version: devel
:Date: |date|
:Manual section: 1

.. |date| date::


SYNOPSYS
========

ghs [options] script ...


DESCRIPTION
===========

`ghs` is a simple Python scripts manager to easily write scripts that interacts
with the GitHub API. It provides scripts with a common configuration that takes
care of authentication and other options, and an easy way to query the GitHub
API.

The utility works out of the box if you don't need to authenticate to GitHub,
otherwise it needs some initial configuration. See the CONFIGURATION_ section
for details.

The *script* to run is looked up in a scripts directory, unless the script
name ends in `.py`, in which case is interpreted as a regular file, so `ghs x`
will look for a file `$script_dir/x.py` while `ghs x.py` will try to open the
file `x.py` in the current directory.

All the arguments after *script* will be passed to the script as is, so the
meaning depends on the different scripts. Please see the `WRITING SCRIPTS`_
section for more details on how to write scripts.


OPTIONS
=======

`ghs` itself accepts some options:

\-h, --help
  show a help message and exit

\--version
  show program's version number and exit

\-c FILE, --config-file FILE
  configuration file to use (default: ~/.ghsrc, /etc/ghsrc)

\-p NAME, --profile NAME
  profile to use from the config file (default: default)

\-v, --verbose
  show verbose output (http requests URLs)

\-d, --debug
  show debug output (complete requests with headers and JSON bodies)

\-b URL, --base-url URL
  base URL to use to make GitHub API requests (default: https://api.github.com)

\-o TOKEN, --oauth-token TOKEN
  GitHub OAuth token to use to authenticate

\-u USER, --username USER
  GitHub username to use to authenticate

\-P PASS, --password PASS
  GitHub password to use to authenticate

\-a MEDIATYPE, --accept MEDIATYPE
  media type to accept (useful to use GitHub API previews) (default:
  application/json)

\-D DIR, --script-dir DIR
  directory where to search for scripts; can be used multiple times, last
  option has priority over the previous ones. The `script_dirs` in the
  configuration file are still used but with the lowest priority.

\-l, --list-scripts
  list available scripts and exit

\-L, --list-all-scripts
  list all scripts, including extra information and broken scripts (prefixed
  with a "!" and a description of why is broken) and exit


WRITING SCRIPTS
===============

`ghs` scripts are just regular Python scripts, except 2 specific symbols are
looked up in them:

`desc`
  A string with a brief description of what the script does. It will be used
  by the `--list-scripts` option.

  If `desc = None` then the Python file will be marked as a non-script (useful
  to add general Python modules acting as general libraries and not intended to
  be used as scripts).

`def main(rq, args, config)`
  The main function executed by `ghs`.

  The `rq` argument is an object to do the requests. The important methods
  are: `head()`, `get()`, `post()`, `patch()`, `put()` and `delete()`. All of
  them take as the first argument a path to the GitHub API, for example
  `rq.get('/repos/github/markup')` will retrieve the information about the
  *markup* repository from the *github* organization. The retrieved data is
  parsed as JSON by the Python's `json.loads()` function, so you can map the
  GitHub API directly as Python objects. You can find a reference to the
  GitHub API here: https://developer.github.com/v3/

  All these methods also accept arbitrary keyword arguments, which are
  translated to keys in a json dictionary to send to GitHub. For example, to
  create a new label for a repository you can do
  `rq.post('/repos/github/markup/labels', name='My label', color='#FF0000')`.
  If arbitrary positional arguments are passed instead, then the contents are
  sent to GitHub as a json list of the items instead of a dictionary.

  The `rq` object also provides access to the especial exception
  `GitHubError`, which is thrown when GitHub reports an error throgh a JSON
  object in the response. You can catch this type of exception and report
  better error messages in your scripts. If you need more details about the
  error you can use its attributes: `message`, `documentation_url` and
  `errors`.

  For advanced users, the `rq` object offer a few more tools:

  * A custom `Accept` header can be used by seting the `accept` attribute. This
    attribute won't change until you update it again.

  * Other custom headers can be added by adding elements to the `headers`
    attribute (`list`). Each element should be a 2-items `tuple` with the
    header name and value (a list is used because for some headers can be
    specified more than once).

  * There is a version of each `get()`, `post()`, etc. that returns also the
    HTTP response (in particular the headers). These fuctions are called
    `get_full()`, `post_full()`, etc. and they return a `tuple` with
    a responses `list` as first element (more than once response can be
    returned if the request was paginated) and the actual JSON obect (same as
    with the nono-\ `_full` versions) as the second element.

  `args` is the raw command line arguments that follows the script in the
  command line call. You can use regular Python facilities to parse the
  arguments, like the `argparse` module.

  `config` is a simple object containing the variables defined in
  CONFIGURATION_, plus `config.prog` which holds the program name, useful to
  pass to an eventual `argparse` for your script.

  Example::

    desc = "Print all the repositories from the github organization"

    def main(rq, args, config):
      for r in rq.get('/orgs/github/repos'):
        print r['name']


CONFIGURATION
=============

`ghs` can be configured to use authentication and an alternative scripts
directory, among other things. The configuration file format is Python too,
you just have to define some special variables. The default location for the
configuration file is `~/.ghsrc`, but it can be overridden by the
`--config-file` command line option.

The most basic configuration uses some predefined global variables:

`debug`
  True to print debug information by default (bool).
  Default: False

`base_url`
  Base URL to use to make GitHub API requests (str). Useful for GitHub
  Enterprise installations.
  Default: 'https://api.github.com'

`script_dirs`
  Default directories where to look for scripts (list of str). Tilde expansions
  are performed (`~` -> your home, `~user` -> `user`\ 's home) over the
  directory names. The first directory in the list is searched first.
  Default: depends on the installation, but usually is ['~/.ghscripts',
  '/usr/share/ghs/scripts'] ('~/.ghscripts' is almost always there).

`oauthtoken`
  OAuth token to access to GitHub (str). You can generate a new OAuth token
  here: https://github.com/settings/tokens/new (depending on the permissions
  you assign to the tokens you'll have access to different GitHub API
  facilities). This configuration takes priority over `username`/`password`
  unless `--username` is used in the command-line (and `--oauth-token` is not
  present).

`username`
  GitHub username (str). A `password` should be provided too if this option is
  used, but it is recommended to use `oauthtoken`\ s instead as you can easily
  revoke them.

`password`
  GitHub password (str). A `username` should be provided too if this option is
  used, but it is recommended to use `oauthtoken`\ s instead as you can easily
  revoke them.

Besides using global variables, you can use *profiles* too. By providing
multiple profiles you can select a different set of options from the command
line by using the `-p` or `--profile` option. This way you can easily pick
from different predefined profiles with possibly different script directories,
credentials and GitHub API base URL (useful to use a work account and a home
account).

To use profiles you need to define a `profiles` variable containing
a dictionary, where the key is the name of the profile and the value is
another dictionary that can contain any of the configuration variables
mentioned before. Global variables in the configuration file then work as
defaults. The `default` profile should be defined, and it's used when no
`--profile` option is passed.

For example::

  debug = True
  profiles = dict(
      admin = dict(
          oauthtoken = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
      ),
      user = dict(
          # Using your user+password is possible but NOT recommended!
          username = "mygithubuser"
          password = "my super secret github password"
      ),
      enterprise = dict(
          base_url = 'https://api.example.com',
          oauthtoken = 'yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy',
      ),
  )
  profiles['default'] = profiles['user']

Any option set in this file is overridden by the corresponding command line
option.


EXIT VALUES
===========

0
  Success

2
  Incorrect command line arguments

3
  Configuration file error

4
  Error while loading the script (syntax error in the script, most likely)

5
  Script not found



FILES
=====

`/etc/ghsrc`, `~/.ghsrc`
  Default configuration files to read. `/etc/ghsrc` is readed first, and its
  values are overriden by `~/.ghsrc`. These files are optional, the program
  won't complain if either don't exist.

`~/.ghscripts`
  Default directory where to look for scripts.

.. vim: set et sw=2 :

