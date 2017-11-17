## Allow overriding of the `Accept` header

This is available for both script writers and users and can be used to query preview GitHub APIs (or even get the replies in other formats).

For users, `ghs` now have a new `--accept` (`-a`) option to override the `Accept` header.

For writers, the `rq` object now has a new attribute `accept` that can be used to override the `Accept` header.
