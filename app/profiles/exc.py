class APIError(Exception):
    """Generic error resulting from upstream provider API"""
    pass


class NotFoundError(APIError):
    """API request resulted in a 404"""
    pass


class ProfileNotFoundError(APIError):
    """Could not find a named profile in an upstream provider API"""
    pass


class UpstreamRateLimit(APIError):
    """Upstream provider API is rate-limiting requests"""
    pass
