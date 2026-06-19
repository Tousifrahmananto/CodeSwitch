from rest_framework.throttling import AnonRateThrottle, SimpleRateThrottle, UserRateThrottle


class ScopeTrackingMixin:
    def allow_request(self, request, view):
        allowed = super().allow_request(request, view)
        if not allowed:
            request._throttle_scope = self.scope
        return allowed


class TrackedUserThrottle(ScopeTrackingMixin, UserRateThrottle):
    pass


class TrackedAnonThrottle(ScopeTrackingMixin, AnonRateThrottle):
    pass


class IPThrottle(ScopeTrackingMixin, SimpleRateThrottle):
    """Apply an IP limit even when the caller is authenticated."""
    def get_cache_key(self, request, view):
        return self.cache_format % {'scope': self.scope, 'ident': self.get_ident(request)}


class AIBurstThrottle(TrackedUserThrottle):
    scope = 'ai_burst'


class AISustainedThrottle(TrackedUserThrottle):
    scope = 'ai_sustained'


class RegisterThrottle(IPThrottle):
    scope = 'register'


class LoginThrottle(IPThrottle):
    scope = 'login'


class TokenRefreshThrottle(IPThrottle):
    scope = 'token_refresh'


class PublicProfileThrottle(IPThrottle):
    scope = 'public_profile'


class RunCodeAnonThrottle(TrackedAnonThrottle):
    scope = 'run_anon'


class RunCodeUserThrottle(TrackedUserThrottle):
    scope = 'run_user'


class SnippetIPThrottle(IPThrottle):
    scope = 'snippet_ip'


class SnippetCreateThrottle(TrackedUserThrottle):
    scope = 'snippet_create'


class WriteThrottle(TrackedUserThrottle):
    scope = 'write'

    def allow_request(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return super().allow_request(request, view)


class AdminThrottle(TrackedUserThrottle):
    scope = 'admin'
