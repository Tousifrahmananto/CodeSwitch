from pathlib import Path
from decouple import config
from datetime import timedelta
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='dev-secret-key-change-in-production')
DEBUG = config('DEBUG', default=True, cast=bool)
# ── ALLOWED_HOSTS Security ────────────────────────────────────────────────────
# IMPORTANT: Use specific domain names only. Wildcards like ".vercel.app" allow any
# subdomain to proxy your backend and are a Host Header Injection vector.
# Example: ALLOWED_HOSTS="myapp.vercel.app,api.railway.app,localhost,127.0.0.1"
_hosts_config = config('ALLOWED_HOSTS', default='localhost,127.0.0.1')
ALLOWED_HOSTS = [h.strip() for h in _hosts_config.split(',') if h.strip()]
if not DEBUG and 'healthcheck.railway.app' not in ALLOWED_HOSTS:
    # Railway sends readiness probes from this host, even when the app's own
    # public Railway domain is configured separately.
    ALLOWED_HOSTS.append('healthcheck.railway.app')
# Security check: warn about wildcards
if any('*' in host or (host.startswith('.') and not DEBUG) for host in ALLOWED_HOSTS):
    import logging
    logging.warning(
        "SECURITY WARNING: ALLOWED_HOSTS contains wildcard patterns. "
        "This may allow Host Header Injection attacks. Use specific domain names instead."
    )

# ── SECRET_KEY guard ──────────────────────────────────────────────────────────
import sys as _sys
if len(SECRET_KEY) < 50 and not any(c in _sys.argv for c in ['test', 'migrate', 'collectstatic']):
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured(
        "SECRET_KEY is dangerously short (< 50 chars). "
        "Generate one: python -c \"from django.core.management.utils import "
        "get_random_secret_key; print(get_random_secret_key())\""
    )
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'axes',         # Brute-force login protection
    # Local apps
    'users',
    'converter',
    'files',
    'learning',
]

AUTH_USER_MODEL = 'users.User'

MIDDLEWARE = [
    'codeswitch.middleware.RequestObservabilityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'csp.middleware.CSPMiddleware',              # Content-Security-Policy headers
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'axes.middleware.AxesMiddleware',            # Must come after AuthenticationMiddleware
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'codeswitch.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'codeswitch.wsgi.application'

# Railway provides DATABASE_URL automatically; fall back to manual config for local dev
_database_url = config('DATABASE_URL', default='')
if _database_url:
    DATABASES = {'default': dj_database_url.parse(_database_url, conn_max_age=600)}
elif config('DB_ENGINE', default='') == 'django.db.backends.postgresql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='codeswitch_db'),
            'USER': config('DB_USER', default='postgres'),
            'PASSWORD': config('DB_PASSWORD', default=''),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
APPEND_SLASH = False  # All API URLs are defined without trailing slashes; disable redirect to avoid POST body loss

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = config('MEDIA_URL', default='/media/')
_media_root = config('MEDIA_ROOT', default='').strip()
MEDIA_ROOT = Path(_media_root) if _media_root else BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        # Reads JWT from httpOnly cookie — tokens never visible to JavaScript
        'users.authentication.JWTCookieAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'EXCEPTION_HANDLER': 'codeswitch.exception_handler.api_exception_handler',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '30/minute',
        'user': '300/minute',
        # AI-endpoint specific throttles (applied per-view via converter/throttles.py)
        'ai_burst':     '5/minute',
        'ai_sustained': '30/hour',
        'run_anon':     '10/minute',
        'register': '5/hour',
        'login': '10/minute',
        'token_refresh': '30/minute',
        'public_profile': '60/minute',
        'run_user': '30/minute',
        'snippet_ip': '60/minute',
        'snippet_create': '20/hour',
        'write': '60/minute',
        'admin': '120/minute',
        'snippet_anon': '60/minute',  # PUBLIC snippet retrieval — prevent UUID enumeration
    },
}

REDIS_URL = config('REDIS_URL', default='').strip()
if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient'},
            'KEY_PREFIX': config('CACHE_KEY_PREFIX', default='codeswitch'),
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'codeswitch-local',
        }
    }

TRUSTED_PROXY_COUNT = config('TRUSTED_PROXY_COUNT', default=0, cast=int)
REST_FRAMEWORK['NUM_PROXIES'] = TRUSTED_PROXY_COUNT
METRICS_ENABLED = config('METRICS_ENABLED', default=True, cast=bool)
METRICS_BEARER_TOKEN = config('METRICS_BEARER_TOKEN', default='')
CONVERSION_HISTORY_RETENTION_DAYS = config('CONVERSION_HISTORY_RETENTION_DAYS', default=180, cast=int)

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=config('JWT_ACCESS_TOKEN_LIFETIME_MINUTES', default=60, cast=int)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=config('JWT_REFRESH_TOKEN_LIFETIME_DAYS', default=7, cast=int)),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

GOOGLE_OAUTH_CLIENT_ID = config('GOOGLE_OAUTH_CLIENT_ID', default='')

# ── CORS Security ────────────────────────────────────────────────────────────
# CRITICAL: Wildcard origins are only safe when credentials are disabled.
# When CORS_ALLOW_CREDENTIALS=True, MUST use explicit origin list only.
CORS_ALLOW_CREDENTIALS = True
def _parse_and_validate_origins(origins_str: str) -> list:
    """Parse comma-separated origins and validate security constraints."""
    origins = [o.strip() for o in origins_str.split(',') if o.strip()]
    # Check for dangerous patterns
    if '*' in origins and CORS_ALLOW_CREDENTIALS:
        import sys
        # ONLY raise on deploy, not during migrations
        if not any(arg in sys.argv for arg in ['migrate', 'collectstatic', 'test']):
            from django.core.exceptions import ImproperlyConfigured
            raise ImproperlyConfigured(
                "SECURITY ERROR: Wildcard CORS origins (*) cannot be used with "
                "CORS_ALLOW_CREDENTIALS=True. Use explicit origins instead: "
                "https://example.com,https://another.com"
            )
    return origins

CORS_ALLOWED_ORIGINS = _parse_and_validate_origins(
    config('CORS_ALLOWED_ORIGINS', default='http://localhost:3000')
)
# Credentials (cookies) must be sent cross-origin — requires explicit origin list (no wildcard)
# Allow the user-provided API key header from the frontend
from corsheaders.defaults import default_headers as _default_cors_headers
CORS_ALLOW_HEADERS = list(_default_cors_headers) + ['X-User-Api-Key']
CSRF_TRUSTED_ORIGINS = _parse_and_validate_origins(
    config('CSRF_TRUSTED_ORIGINS', default='http://localhost:8000')
)

# ── Cookie security ───────────────────────────────────────────────────────────
SESSION_COOKIE_HTTPONLY = True
# Cross-origin production (Vercel → Railway): SameSite=None so cookies are sent cross-site.
# Local development: SameSite=Lax is sufficient (both services run on localhost).
SESSION_COOKIE_SAMESITE = 'None' if not DEBUG else 'Lax'
# In production these are forced True by SECURE_SSL_REDIRECT
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = False   # Must be JS-readable so Axios can send X-CSRFToken header
CSRF_COOKIE_SAMESITE = 'None' if not DEBUG else 'Lax'
CSRF_COOKIE_SECURE = not DEBUG

# ── Security headers ──────────────────────────────────────────────────────────
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
# Railway (and most PaaS) terminates SSL at the load balancer and forwards to
# Django over plain HTTP internally. Setting SECURE_SSL_REDIRECT=True causes an
# infinite redirect loop. Instead, trust the X-Forwarded-Proto header so Django
# knows the original request was HTTPS without redirecting itself.
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ── Logging ───────────────────────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {'format': '{levelname} {asctime} {module} {message}', 'style': '{'},
        'json': {'()': 'codeswitch.logging_config.JsonFormatter'},
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json' if config('LOG_FORMAT', default='console') == 'json' else 'verbose',
        },
    },
    'root': {'handlers': ['console'], 'level': config('LOG_LEVEL', default='INFO')},
    'loggers': {
        'django.security': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
        'axes':            {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
        'codeswitch':      {'handlers': ['console'], 'level': 'INFO',    'propagate': False},
    },
}

# ── Content Security Policy (django-csp) ─────────────────────────────────────
# Monaco Editor requires 'unsafe-eval' for script execution and blob: for workers.
CSP_DEFAULT_SRC    = ("'none'",)
CSP_SCRIPT_SRC     = ("'self'", "'unsafe-eval'")
CSP_STYLE_SRC      = ("'self'", "'unsafe-inline'", "https://fonts.googleapis.com")
CSP_FONT_SRC       = ("'self'", "https://fonts.gstatic.com")
CSP_IMG_SRC        = ("'self'", "data:", "blob:")
CSP_CONNECT_SRC    = ("'self'", "https://wandbox.org")
CSP_WORKER_SRC     = ("'self'", "blob:")   # Monaco editor uses blob: workers
CSP_FRAME_ANCESTORS = ("'none'",)
CSP_FORM_ACTION    = ("'self'",)
CSP_BASE_URI       = ("'none'",)

# ── Brute-force protection (django-axes) ─────────────────────────────────────
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]
AXES_ENABLED                 = config('AXES_ENABLED', default=True, cast=bool)
AXES_FAILURE_LIMIT           = 5       # Lock after 5 failed attempts
AXES_COOLOFF_TIME            = 1       # Unlock after 1 hour
AXES_LOCKOUT_PARAMETERS      = ['username', 'ip_address']
AXES_RESET_ON_SUCCESS        = True
AXES_IPWARE_PROXY_COUNT = TRUSTED_PROXY_COUNT
AXES_IPWARE_META_PRECEDENCE_ORDER = (
    ['HTTP_X_FORWARDED_FOR', 'REMOTE_ADDR'] if TRUSTED_PROXY_COUNT > 0 else ['REMOTE_ADDR']
)
