## Many improvements to the `rq` script (and its aliases)

`rq`, `get`, `head`, `post`, `put`, `patch`

* Allow values to be empty when using `key=val` (use `key=`).

* New `--format` (`-f`) option allows arbitrary formatting.

  JSON responses are converted to Python lists/dictionaries and the standard Python `format()` function is used for formatting. Any field from the response can be used.
  
  If the response is a single object, each attribute is passed to the `format()` function as `key=value`, so it can be accessed like `{key}` in the formatting string.

  If the response is a `list`, then the format string is applied to every element in the list. An additional positional argument with the list index is passed, which can be used as `{0}` in the formatting string.

  By default the complete JSON Response is printed as before.

  This makes those script much more usable while writing shell scripts.

  For more details see: https://docs.python.org/3/library/string.html#formatstrings. 
  
* Allow `True`/`False` values

  If a value is passed as `true` or `false` (case insensitive), the it is interpreted as a JSON bool value and passed as such. If you want to specify a string `"true"` or `"false"` just explicitly quote it, for example: `ghs get orgs 'key="true"'`.
