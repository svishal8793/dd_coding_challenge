import logging

import flask
import flask.logging

from app.profiles import (
    aggregate_profile_metrics,
    BitbucketProfileSummary,
    GitHubProfileSummary,
    ProfileNotFoundError,
    UpstreamRateLimit
)


app = flask.Flask("user_profiles_api")
logger = flask.logging.create_logger(app)
logger.setLevel(logging.INFO)


@app.route("/health-check", methods=["GET"])
def health_check():
    """Handles a request to retrieve metrics for one or more supported Git services. If multiple usernames are
    provided in the incoming request, metrics from all profiles will be aggregated in the response.

    :return: A response containing an aggregation of one or more Git profile metrics
    :rtype: flask.Response
    """
    profiles = parse_username_argument(flask.request.args, 'github_usernames', GitHubProfileSummary)
    profiles.extend(parse_username_argument(flask.request.args, 'bitbucket_usernames', BitbucketProfileSummary))

    aggregated_metrics = aggregate_profile_metrics(profiles)
    response = flask.jsonify(aggregated_metrics)

    app.logger.info("Successfully fetch the metrices.")
    return response


@app.errorhandler(UpstreamRateLimit)
def handle_upstream_rate_limit(e):
    """Handles :cls:`UpstreamRateLimit` exceptions caught by Flask

    :param e: The exception caught by Flask during the current request/response cycle
    :type e: UpstreamRateLimit
    :return: A JSON response which informs the user that an upstream API provider is rate-limiting requests
        from this service
    :rtype: flask.Response
    """
    logger.error(f'Rate-limiting detected for API: {e}')
    response = flask.jsonify(
        {
            'error': f'Upstream {e} API is refusing to serve requests due to rate limit violation. Try again later.'
        }
    )
    response.status_code = 503
    return response


@app.errorhandler(ProfileNotFoundError)
def handle_profile_not_found(e):
    """Handles :cls:`ProfileNotFoundError` exceptions caught by Flask

    :param e: The exception caught by flask during the current request/response cycle. This error is expected to
        provide a message which includes the API for which the username was not found as well as the username.
    :type e: ProfileNotFoundError
    :return: A JSON response which wraps the message provided by the caught exception
    :rtype: flask.Response
    """
    response = flask.jsonify({'error': str(e)})
    response.status_code = 404
    return response


def parse_username_argument(request_args, username_key, profile_cls):
    """Initializes and validates :cls:`app.profiles.profiles.ProfileSummary` implementations based
    on provided HTTP request data.

    :param request_args: The query string arguments provided by an HTTP request being handled
    :type request_args: dict
    :param username_key: The request argument parameter name from which values should be parsed and used
        to initialize a corresponding :cls:`~app.profiles.profiles.ProfileSummary` object
    :type username_key: str
    :param profile_cls: The :cls:`app.profiles.profiles.ProfileSummary` implementation type from which objects
        will be instantiated with each unique parsed username
    :type profile_cls: type
    :return: A list of validated, de-duplicated Git service profile objects
    :rtype: list[app.profiles.profiles.ProfileSummary]
    """
    if not request_args.get(username_key):
        return []

    profiles = []
    delimiter = request_args.get('username_delimiter', ',')

    usernames = {username.strip() for username in request_args[username_key].split(delimiter)}
    for username in usernames:
        profile = profile_cls(username)
        profile.validate_username()
        logger.info(f'Parsed validated {profile.PROVIDER} profile: {profile.username}')
        profiles.append(profile)

    return profiles

