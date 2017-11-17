## New `GitHubError` available to scripts

The `rq` object also provides access to the especial exception `GitHubError`, which is thrown when GitHub reports an error throgh a JSON object in the response. You can catch this type of exception and report better error messages in your scripts. If you need more details about the error you can use its attributes: `message`, `documentation_url` and `errors`.
