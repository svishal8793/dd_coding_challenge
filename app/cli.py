import argparse
import json
import sys

from app.profiles import (
    aggregate_profile_metrics,
    BitbucketProfileSummary,
    GitHubProfileSummary,
    ProfileNotFoundError,
    UpstreamRateLimit
)

EXIT_SUCCESS = 0
EXIT_FAILURE = 1


def _get_parsed_arguments():
    parser = argparse.ArgumentParser(
        description='Generates detailed metrics for one or more specified Git service profiles',
        usage='python -m app.cli'
    )
    parser.add_argument(
        '-g',
        '--github-username',
        dest='github_usernames',
        nargs='*',
        type=GitHubProfileSummary,
        default=[],
        help=(
            '(Optional) One or more GitHub usernames from which metrics will be aggregated '
            'into the resulting metric report'
        )
    )
    parser.add_argument(
        '-b',
        '--bitbucket-username',
        dest='bitbucket_usernames',
        nargs='*',
        type=BitbucketProfileSummary,
        default=[],
        help=(
            '(Optional) One or more Bitbucket usernames from which metrics will be aggregated '
            'into the resulting metric report'
        )
    )
    parser.add_argument(
        '-o',
        '--outfile',
        dest='outfile',
        type=argparse.FileType('w'),
        default=sys.stdout,
        help='(Optional) Where the report of aggregated metrics should be written. Defaults to STDOUT.'
    )
    return parser.parse_args()


def validate_profiles(git_profiles):
    for profile in git_profiles:
        profile.validate_username()


def _main():
    args = _get_parsed_arguments()
    profiles = args.github_usernames + args.bitbucket_usernames

    try:
        validate_profiles(profiles)
        aggregated_metrics = aggregate_profile_metrics(profiles)
    except ProfileNotFoundError as e:
        print(f'ERROR: {e}', file=sys.stderr)
        return EXIT_FAILURE
    except UpstreamRateLimit as e:
        print(
            f'ERROR: Upstream {e} API is refusing to serve requests due to rate limit violation. Try again later.',
            file=sys.stderr
        )
        return EXIT_FAILURE

    json.dump(aggregated_metrics, args.outfile, indent=2)
    return EXIT_SUCCESS


if __name__ == '__main__':
    sys.exit(_main())
