from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    """
    Rate limit login attempts to prevent brute force attacks
    """
    scope = 'login'


class CommentRateThrottle(UserRateThrottle):
    """
    Rate limit comment creation to prevent spam
    """
    scope = 'comment'


class BurstRateThrottle(UserRateThrottle):
    """
    Allow short bursts of requests (for UI interactions)
    """
    scope = 'burst'
    rate = '60/minute'