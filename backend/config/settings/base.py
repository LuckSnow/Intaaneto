"""
Django base settings for Intaaneto project.
"""

from pathlib import Path
from decouple import config
from datetime import timedelta

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    
    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'drf_yasg',
    'social_django',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    
    # Email
    'anymail',
    
    # Local apps
    'apps.users',
    'apps.courses',
    'apps.exercises',
    'apps.ai_assistant',
    'apps.forum',
    'apps.analytics',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # Must be before CommonMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'config.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='intaaneto_db'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='postgres'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'vi'
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files (User uploads)
MEDIA_URL = config('MEDIA_URL', default='/media/')
MEDIA_ROOT = BASE_DIR / config('MEDIA_ROOT', default='media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=config('JWT_ACCESS_TOKEN_LIFETIME', default=60, cast=int)),
    'REFRESH_TOKEN_LIFETIME': timedelta(minutes=config('JWT_REFRESH_TOKEN_LIFETIME', default=1440, cast=int)),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# CORS Settings
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:5173,http://127.0.0.1:5173',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

# AI Tutor generation provider
AI_GENERATION_PROVIDER = config('AI_GENERATION_PROVIDER', default='openai').lower()
OPENAI_API_KEY = config('OPENAI_API_KEY', default='')
GEMINI_API_KEY = config('GEMINI_API_KEY', default='')
GEMINI_BASE_URL = config(
    'GEMINI_BASE_URL',
    default='https://generativelanguage.googleapis.com/v1beta/openai/',
)
AI_GENERATION_MODEL = config('AI_GENERATION_MODEL', default='gpt-4o-mini')
GEMINI_GENERATION_MODEL = config(
    'GEMINI_GENERATION_MODEL',
    default='gemini-3.1-flash-lite',
)
AI_REQUEST_TIMEOUT_SECONDS = config('AI_REQUEST_TIMEOUT_SECONDS', default=30, cast=int)
AI_MAX_HISTORY_MESSAGES = config('AI_MAX_HISTORY_MESSAGES', default=12, cast=int)

# RAG lesson indexing
RAG_EMBEDDING_MODEL = config(
    'RAG_EMBEDDING_MODEL',
    default='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
)
RAG_EMBEDDING_REVISION = config(
    'RAG_EMBEDDING_REVISION',
    default='fastembed-0.8.0-mean-pooling',
)
RAG_EMBEDDING_DIMENSION = config('RAG_EMBEDDING_DIMENSION', default=384, cast=int)
RAG_CHUNK_SIZE = config('RAG_CHUNK_SIZE', default=1000, cast=int)
RAG_CHUNK_OVERLAP = config('RAG_CHUNK_OVERLAP', default=150, cast=int)
RAG_MAX_CHUNKS_PER_SOURCE = config('RAG_MAX_CHUNKS_PER_SOURCE', default=500, cast=int)
RAG_RETRIEVAL_TOP_K = config('RAG_RETRIEVAL_TOP_K', default=5, cast=int)
RAG_RETRIEVAL_MAX_TOP_K = config('RAG_RETRIEVAL_MAX_TOP_K', default=10, cast=int)
RAG_RETRIEVAL_MIN_SCORE = config('RAG_RETRIEVAL_MIN_SCORE', default=0.45, cast=float)
RAG_MAX_QUESTION_CHARS = config('RAG_MAX_QUESTION_CHARS', default=1000, cast=int)
RAG_GENERATION_MAX_EVIDENCE_CHUNKS = config(
    'RAG_GENERATION_MAX_EVIDENCE_CHUNKS',
    default=3,
    cast=int,
)
RAG_GENERATION_MAX_CONTEXT_CHARS = config(
    'RAG_GENERATION_MAX_CONTEXT_CHARS',
    default=6000,
    cast=int,
)
RAG_CITATION_EXCERPT_CHARS = config(
    'RAG_CITATION_EXCERPT_CHARS',
    default=320,
    cast=int,
)

# Groq API Key (Llama)
GROQ_API_KEY = config('GROQ_API_KEY', default='')

# D-ID API Key (base64 encoded email:key)
DID_API_KEY = config('DID_API_KEY', default='')

# Firebase
FIREBASE_PROJECT_ID = config('FIREBASE_PROJECT_ID', default='')

# Security Settings
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB
LESSON_PDF_MAX_BYTES = config('LESSON_PDF_MAX_BYTES', default=20 * 1024 * 1024, cast=int)
LESSON_PDF_MAX_PAGES = config('LESSON_PDF_MAX_PAGES', default=100, cast=int)
LESSON_PDF_MAX_EXTRACTED_CHARS = config(
    'LESSON_PDF_MAX_EXTRACTED_CHARS',
    default=250000,
    cast=int,
)

# Email Configuration - Mailjet via Anymail
EMAIL_BACKEND = config('EMAIL_BACKEND', default='anymail.backends.mailjet.EmailBackend')
ANYMAIL = {
    'MAILJET_API_KEY': config('MAILJET_API_KEY', default=''),
    'MAILJET_SECRET_KEY': config('MAILJET_SECRET_KEY', default=''),
}
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@intaaneto.com')
SERVER_EMAIL = DEFAULT_FROM_EMAIL
EMAIL_VERIFICATION_TOKEN_TTL_HOURS = config(
    'EMAIL_VERIFICATION_TOKEN_TTL_HOURS',
    default=24,
    cast=int,
)

# Frontend URL for email links
FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:5173')

# Django Sites Framework
SITE_ID = 1

# Social Auth - Google OAuth
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'APP': {
            'client_id': config('GOOGLE_OAUTH_CLIENT_ID', default=''),
            'secret': config('GOOGLE_OAUTH_CLIENT_SECRET', default=''),
            'key': ''
        }
    }
}

# Allauth settings
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_USERNAME_REQUIRED = False
