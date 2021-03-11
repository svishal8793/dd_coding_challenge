import abc
from collections import defaultdict

from app.profiles import exc

import requests


class ProfileSummary(abc.ABC):
    """Abstract base class that specifies an interface for retrieving profile data for a Git service"""
    BASE_URL = NotImplemented
    PROVIDER = NotImplemented

    def __init__(self, username):
        """Initializes a new Git profile summary for a given user

        :param username: The username which identifies a Git profile
        :type username: str
        """
        self.username = username
        self._session = requests.Session()
        self._loaded_state = {}

    def __repr__(self):
        return f'<{self.__class__.__name__} for {self.username}>'

    def reset(self):
        """Resets all data which has been retrieved from a remote API and bound to the current instance state
        """
        self._loaded_state.clear()

    @property
    @abc.abstractmethod
    def _username_validation_url(self):
        """A property for which implementations must provide a valid URL for the configured API
        which used to determine whether the bound :attr:`username` attribute is valid.

        By default (unless overridden by :meth:`validate_username`), this URL must respond to HEAD requests
        with a 404 status code to indicate that a username name is invalid or a 200 status code to indicate that
        that a username is valid.
        """

    def validate_username(self):
        """Determines whether the username bound to the current instance identifies a user within the configured API

        :return: True if the bound username is a valid identifier for a user in the configured API
        :rtype: bool
        :raises exc.ProfileNotFoundError: If the bound username attribute does not identify a user
            in the configured API
        """
        rs = self._handle_response(self._session.head(self._username_validation_url), (200, 404))

        if rs.status_code == 404:
            raise exc.ProfileNotFoundError(f'{self.PROVIDER} could not find a profile for user: {self.username}')

        return True

    def _handle_response(self, response, acceptable_status_codes=(200,)):
        """Ensures a response matches one or more acceptable status codes. If a response with an unacceptable
        status code is encountered, an appropriate error is raised.

        :param response: The response to handle
        :type response: requests.Response
        :param acceptable_status_codes: All acceptable status codes for the given request
        :type acceptable_status_codes: list | tuple | set
        :return: The provided, handled response
        :rtype: requests.Response
        :raises exc.UpstreamRateLimit: When the response indicates that the upstream API is rate-limiting this service
        :raises exc.APIError: When the response provides an unacceptable status code that cannot be more 
            handled with a higher level of granularity 
        """
        if response.status_code not in acceptable_status_codes:
            if response.status_code == 403:
                raise exc.UpstreamRateLimit(self.PROVIDER)
            else:
                raise exc.APIError(
                    f'Received unexpected response for {response.request.method} '
                    f'request to {response.request.url}: {response.status_code}'
                )

        return response

    @abc.abstractmethod
    def _get_next_linked_url(self, response):
        """Extracts the next URL in a paginated response
        
        :param response: The paginated response object
        :type response: requests.Response
        """
        pass

    @property
    @abc.abstractmethod
    def count_stars_given(self):
        """
        :return: The number of stars/likes/kudos/etc given to another repository by the configured user
        :rtype: int
        """

    @property
    @abc.abstractmethod
    def count_stars_received(self):
        """
        :return: The number of stars/likes/kudos/etc given to all repositories owned by the configured user
        :rtype: int
        """

    @property
    @abc.abstractmethod
    def count_original_public_repositories(self):
        """
        :return: The number of all non-forked, public repositories owned by the configured user
        :rtype: int
        """

    @property
    @abc.abstractmethod
    def count_forked_public_repositories(self):
        """
        :return: The number of all forked, public repositories owned by the configured user
        :rtype: int
        """

    @property
    @abc.abstractmethod
    def count_open_issues(self):
        """
        :return: The number of open issues across all repositories owned by the configured user
        :rtype: int
        """

    @property
    @abc.abstractmethod
    def count_followers(self):
        """
        :return: The number of users following the configured user
        :rtype: int
        """

    @property
    @abc.abstractmethod
    def repositories_per_language(self):
        """
        :return: A dictionary keyed by a language that evaluates to a count of repositories
            which are labelled with that language and owned by the configured user
        :rtype: dict
        """

    @property
    @abc.abstractmethod
    def repositories_per_topic(self):
        """
        :return: A dictionary keyed by a topic that evaluates to a count of repositories
            which are labelled with that topic and owned by the configured user
        :rtype: dict
        """


class GitHubProfileSummary(ProfileSummary):
    """Represents a summary for a GitHub user profile"""
    BASE_URL = 'https://api.github.com'
    PROVIDER = 'GitHub'

    @property
    def _username_validation_url(self):
        return f'{self.BASE_URL}/users/{self.username}'

    @property
    def count_stars_given(self):
        return len(self.starred_repositories)

    @property
    def count_stars_received(self):
        return sum(repo['stargazers_count'] for repo in self.public_repositories)

    @property
    def starred_repositories(self):
        """
        .. note:: The return value of this method is cached after the first call until :meth:`reset` is called

        :return: A list of all repositories starred by the configured user
        :rtype: list[dict]
        """
        try:
            starred_repositories = self._loaded_state['starred_repositories']
        except KeyError:
            starred_repositories = []
            next_url = f'{self.BASE_URL}/users/{self.username}/starred'
            while next_url:
                rs = self._handle_response(self._session.get(next_url))
                starred_repositories.extend(rs.json())
                next_url = self._get_next_linked_url(rs)

            self._loaded_state['starred_repositories'] = starred_repositories

        return starred_repositories

    @property
    def public_repositories(self):
        """
        .. note:: The return value of this method is cached after the first call until :meth:`reset` is called

        :return: A list of all public repositories owned by the configured user
        :rtype: list[dict]
        """
        try:
            public_repositories = self._loaded_state['public_repositories']
        except KeyError:
            public_repositories = []
            next_url = f'{self.BASE_URL}/users/{self.username}/repos'
            while next_url:
                rs = self._handle_response(
                    self._session.get(next_url, headers={'Accept': 'application/vnd.github.mercy-preview+json'})
                )
                public_repositories.extend(rs.json())
                next_url = self._get_next_linked_url(rs)

            self._loaded_state['public_repositories'] = public_repositories

        return public_repositories

    @property
    def count_original_public_repositories(self):
        return len([repo for repo in self.public_repositories if not repo['fork']])

    @property
    def count_forked_public_repositories(self):
        return len([repo for repo in self.public_repositories if repo['fork']])

    @property
    def count_open_issues(self):
        return sum(repo['open_issues_count'] for repo in self.public_repositories)

    @property
    def count_followers(self):
        try:
            count_followers = self._loaded_state['count_followers']
        except KeyError:
            count_followers = 0
            next_url = f'{self.BASE_URL}/users/{self.username}/followers'
            while next_url:
                rs = self._handle_response(self._session.get(next_url, params={'per_page': 100}))
                count_followers += len(rs.json())
                next_url = self._get_next_linked_url(rs)

            self._loaded_state['count_followers'] = count_followers

        return count_followers

    @property
    def repositories_per_language(self):
        languages = defaultdict(int)
        for repo in self.public_repositories:
            languages[repo.get('language') or 'UNKNOWN'] += 1

        return languages

    @property
    def repositories_per_topic(self):
        topics = defaultdict(int)
        for repo in self.public_repositories:
            for topic in repo.get('topics', ()):
                topics[topic] += 1

        return topics

    def _get_next_linked_url(self, response):
        try:
            return response.links['next']['url']
        except KeyError:
            return None


class BitbucketProfileSummary(ProfileSummary):
    BASE_URL = 'https://api.bitbucket.org/2.0'
    PROVIDER = 'Bitbucket'

    @property
    def _username_validation_url(self):
        return f'{self.BASE_URL}/users/{self.username}'

    @property
    def count_stars_given(self):
        return 0

    @property
    def count_stars_received(self):
        return 0

    @property
    def public_repositories(self):
        """
        .. note:: The return value of this method is cached after the first call until :meth:`reset` is called

        :return: A list of all public repositories owned by the configured user
        :rtype: list[dict]
        """
        try:
            public_repositories = self._loaded_state['public_repositories']
        except KeyError:
            public_repositories = []
            next_url = f'{self.BASE_URL}/repositories/{self.username}'
            while next_url:
                rs = self._handle_response(self._session.get(next_url, params={'pagelen': 100}))
                public_repositories.extend(rs.json()['values'])
                next_url = self._get_next_linked_url(rs)

            self._loaded_state['public_repositories'] = public_repositories

        return public_repositories

    @property
    def count_original_public_repositories(self):
        return len([repo for repo in self.public_repositories if not repo.get('parent')])

    @property
    def count_forked_public_repositories(self):
        return len([repo for repo in self.public_repositories if repo.get('parent')])

    @property
    def count_open_issues(self):
        try:
            count_open_issues = self._loaded_state['count_open_issues']
        except KeyError:
            count_open_issues = sum(
                self._handle_response(
                    self._session.get(repo['links']['issues']['href'], params={'fields': 'size', 'q': 'state="open"'})
                ).json()['size']
                for repo in self.public_repositories if repo['has_issues']
            )

            self._loaded_state['count_open_issues'] = count_open_issues

        return count_open_issues

    @property
    def count_followers(self):
        try:
            count_followers = self._loaded_state['count_followers']
        except KeyError:
            rs = self._handle_response(
                self._session.get(f'{self.BASE_URL}/users/{self.username}/followers', params={'fields': 'size'})
            )
            count_followers = rs.json()['size']
            self._loaded_state['count_followers'] = count_followers

        return count_followers

    @property
    def repositories_per_language(self):
        languages = defaultdict(int)
        for repo in self.public_repositories:
            languages[repo.get('language') or 'UNKNOWN'] += 1

        return languages

    @property
    def repositories_per_topic(self):
        """
        .. note:: Topics are unsupported by Bitbucket
        """
        return {}

    def _get_next_linked_url(self, response):
        try:
            return response.json()['next']
        except KeyError:
            return None
