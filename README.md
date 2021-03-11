# Coding Challenge App

A skeleton flask app to use for a coding challenge.

## Install:

You can use a virtual environment (conda, venv, etc):
```
conda env create -f environment.yml
source activate user-profiles
```

Or just pip install from the requirements file
``` 
pip install -r requirements.txt
```

## Running the code
python -m run.py

### Spin up the service

```
# start up local server
python -m run 
```

### Making Requests

```
curl -i "http://127.0.0.1:5000/health-check"

A single endpoint is provided by this API: `<BASE URL>/health-check`. When making requests to this endpoint,
you can include the following querystring parameters, all of which are optional:

- `github_usernames`: One or more valid GitHub profile usernames to include in the aggregated metrics response.
Multiple values should be separated with a comma by default.
-  `bitbucket_usernames`: One or more valid Bitbucket profile usernames to include in the aggregated metrics response.
Multiple values should be separated with a comma by default.
- `username_delimiter`: A character by which multiple provided GitHub and Bitbucket usernames will be delimited.
By default, the API expects comma-separated values, but you can use this parameter to override the behavior.
Note that if you are only aggregating (up to) one GitHub and Bitbucket profile each, setting this parameter has no 
effect.
```

## Invoking CLI
 Show usage details:
    ```bash
    $ python -m app.cli --help
    ```
- Get metrics for a single GitHub user:
    ```bash
    $ python -m app.cli --github-username MyUsername
    ```

## What'd I'd like to improve on...
