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


class CsrfTokenThrottle(IPThrottle):
    scope = 'csrf'


class PublicProfileThrottle(IPThrottle):
    scope = 'public_profile'


class RunCodeAnonThrottle(TrackedAnonThrottle):
    scope = 'run_anon'


class RunCodeUserThrottle(TrackedUserThrottle):
    scope = 'run_user'


class RunCodeAnonSustainedThrottle(TrackedAnonThrottle):
    scope = 'run_anon_sustained'


class RunCodeUserSustainedThrottle(TrackedUserThrottle):
    scope = 'run_user_sustained'


class VerifyBurstThrottle(TrackedUserThrottle):
    scope = 'verify_burst'


class VerifySustainedThrottle(TrackedUserThrottle):
    scope = 'verify_sustained'


class VisualizerBurstThrottle(TrackedUserThrottle):
    scope = 'visualizer_burst'


class VisualizerSustainedThrottle(TrackedUserThrottle):
    scope = 'visualizer_sustained'


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


class ProfileWriteThrottle(WriteThrottle):
    scope = 'profile_write'


class FileWriteThrottle(WriteThrottle):
    scope = 'file_write'


class QuizSubmitThrottle(TrackedUserThrottle):
    scope = 'quiz_submit'


class HistoryReadThrottle(TrackedUserThrottle):
    scope = 'history_read'


class AdminThrottle(TrackedUserThrottle):
    scope = 'admin'
