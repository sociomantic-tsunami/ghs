## New `rq` methods that also return the response(s)

To be able to make advance usage of GitHub API sometimes is necessary to access the response headers (to use `ETag`s for example).

The new methods are: `json_req_full()`, `get_full()`, `head_full()`, `put_full()`, `post_full()`, `patch_full()` and `delete_full()`.

They return a `tuple` where the first element is a list of responses objects (more than one can be returned if the request was paginated) and the second one the parsed JSON object.
