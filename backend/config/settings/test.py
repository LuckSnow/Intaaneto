"""Fast, isolated settings used by the automated test suite."""

from .base import *  # noqa: F401,F403


DEBUG = False
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
ANYMAIL = {}

# Throttle behavior has dedicated tests. Keep unrelated tests isolated from the
# shared cache, whose keys intentionally outlive database transaction rollbacks.
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    'DEFAULT_THROTTLE_RATES': {
        scope: '1000000/minute'
        for scope in REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']
    },
}
