def aggregate_profile_metrics(profiles):
    """Creates a report of metrics derived from a list of Git service profile objects

    :param profiles: The profiles for which a metric report should be aggregated
    :type profiles: list[app.profiles.profiles.ProfileSummary]
    :return: A JSON-safe dictionary containing all aggregated metrics
    :rtype: dict
    """
    metrics = {
        'public_repositories': {
            'original': 0,
            'forked': 0
        },
        'watchers': 0,
        'stars_received': 0,
        'stars_given': 0,
        'open_issues': 0,
        'languages': set(),
        'topics': set()
    }

    for profile in profiles:
        metrics['public_repositories']['original'] += profile.count_original_public_repositories
        metrics['public_repositories']['forked'] += profile.count_forked_public_repositories
        metrics['watchers'] += profile.count_followers
        metrics['stars_received'] += profile.count_stars_received
        metrics['stars_given'] += profile.count_stars_given
        metrics['open_issues'] += profile.count_open_issues
        metrics['languages'].update(profile.repositories_per_language.keys())
        metrics['topics'].update(profile.repositories_per_topic.keys())

    metrics['languages'] = tuple(metrics['languages'])
    metrics['topics'] = tuple(metrics['topics'])

    return metrics
