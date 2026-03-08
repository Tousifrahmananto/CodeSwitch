from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class AIBurstThrottle(UserRateThrottle):
    """5 AI requests per minute per user — prevents rapid fire conversions."""
    scope = 'ai_burst'


class AISustainedThrottle(UserRateThrottle):
    """30 AI requests per hour per user — prevents sustained API abuse."""
    scope = 'ai_sustained'


class RunCodeAnonThrottle(AnonRateThrottle):
    """10 code-run requests per minute for anonymous users."""
    scope = 'run_anon'
