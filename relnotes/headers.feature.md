## Allow sending custom headers in GitHub requests

Now script writers can use a new `headers` attribute in `rq` that allows for adding extra headers to the request. With this is possible to send `If-Modified-Since` or `ETag` headers to use a cache or other advanced uses.
