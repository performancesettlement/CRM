"""
Django settings for lotonow project.

"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import local_config as local_config

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'u&7+n(-uzr!7zif38%(722jr@+j^170_)q(&%+kc5v6x@%v505'

SITE_DOMAIN = local_config.SITE_DOMAIN
ALLOWED_HOSTS = local_config.ALLOWED_HOSTS
SITE_HOST = local_config.HOST
DEBUG = local_config.DEBUG
ADDRESS_API_KEY = local_config.ADDRESS_API_KEY
DATABASE_NAME = local_config.DATABASE_NAME
DATABASE_USER = local_config.DATABASE_USER
DATABASE_HOST = local_config.DATABASE_HOST
DATABASE_PORT = local_config.DATABASE_PORT
DATABASE_PASSWORD = local_config.DATABASE_PASSWORD

INDEX_PAGE = '/account/login/'

LOGIN_URL = '/account/login/'

ADMIN_MEDIA_PREFIX = '/static/admin/'

SITE_ID = 2

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'django.contrib.sites',
    'django_crontab',
    'elasticsearch',
    'haystack',
    'django_auth_app',
    'sundog',
    'rest_framework',
    'compressor',
    'taggit',
    'wagtail.wagtailcore',
    'wagtail.wagtailadmin',
    'wagtail.wagtaildocs',
    'wagtail.wagtailsnippets',
    'wagtail.wagtailusers',
    'wagtail.wagtailimages',
    'wagtail.wagtailembeds',
    'wagtail.wagtailsearch',
    'wagtail.wagtailredirects',
    'wagtail.wagtailforms',
    'wagtail.wagtailsites',
    'wagtail.contrib.wagtailapi',
    'avatar',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.twitter',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',

    'wagtail.wagtailcore.middleware.SiteMiddleware',
    'wagtail.wagtailredirects.middleware.RedirectMiddleware',
    'sundog.middleware.TimezoneMiddleware',
    'sundog.middleware.ImpersonationMiddleware'
)

ROOT_URLCONF = 'sundog.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(PROJECT_ROOT, 'django_auth_app', 'templates'),
            os.path.join(PROJECT_ROOT, 'django_auth_app/templates', 'registration'),
            os.path.join(PROJECT_ROOT, 'django_auth_app/templates', 'account'),
            os.path.join(PROJECT_ROOT, 'django_auth_app/templates', 'mail'),
            os.path.join(PROJECT_ROOT, 'sundog', 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.core.context_processors.i18n',
                'django.core.context_processors.debug',
                'django.core.context_processors.request',
                'django.core.context_processors.media',
                'django.core.context_processors.csrf',
                'django.core.context_processors.tz',
                'django.core.context_processors.static',
                'sundog.context_processors.recent_files',
                'django.template.context_processors.request',
            ],
        },
    },
]

AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',

    # `allauth` specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',
)

SOCIALACCOUNT_PROVIDERS = {
    'facebook': {
        'METHOD': 'oauth2',
        'SCOPE': ['email', 'public_profile'],
        'AUTH_PARAMS': {'auth_type': 'reauthenticate'},
        'FIELDS': [
          'id',
          'email',
          'name',
          'first_name',
          'last_name',
          'verified',
          'locale',
          'timezone',
          'link',
          'gender',
          'updated_time'],
        'EXCHANGE_TOKEN': True,
        'LOCALE_FUNC': lambda request: 'en_US',
        'VERIFIED_EMAIL': False,
        'VERSION': 'v2.4'
        }
    }

WSGI_APPLICATION = 'sundog.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': DATABASE_NAME,
        'USER': DATABASE_USER,
        'PASSWORD': DATABASE_PASSWORD,
        'HOST': DATABASE_HOST,
        'PORT': DATABASE_PORT,
    }
}

TEST_RUNNER = 'sundog.test_runner.NoDbTestRunner'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/var/tmp/django_cache',
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'info_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(PROJECT_ROOT, 'log', 'sundog.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5 mb
            'backupCount': 10,
            'formatter': 'verbose'
        },
        'mail': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'formatter': 'verbose',
        },
        'syslog': {
            'level': 'DEBUG',
            'class': 'logging.handlers.SysLogHandler',
            'facility': 'local5',
            'formatter': 'simple'
        },
        'django': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(PROJECT_ROOT, 'log', 'django.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5 mb
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'sundog': {
            'handlers': ['info_file', 'mail', 'syslog'],
            'level': 'DEBUG',
        },
        'django_auth_app': {
            'handlers': ['info_file', 'mail', 'syslog'],
            'level': 'DEBUG',
        },
        'django': {
            'handlers': ['syslog', 'django'],
            'level': 'WARNING',
            'propagate': True,
        },
        'django.db.backends': {
            'handlers': ['syslog', 'django'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['syslog', 'mail', 'django'],
            'level': 'INFO',
            'propagate': True,
        },
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

WAGTAIL_SITE_NAME = 'SunDog'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'media')
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static')

LOGIN_REDIRECT_URL = '/home/'

# email

NO_REPLY_EMAIL_ADDRESS = "careers@mahisoft.com"
INFO_EMAIL_ADDRESS = "careers@mahisoft.com"
TO_CONTACT_INFO_EMAIL_ADDRESS = "careers@mahisoft.com"

EMAIL_HOST = 'email-smtp.us-east-1.amazonaws.com'
EMAIL_PORT = 2587
EMAIL_HOST_USER = 'AKIAIJLAJXAWTVFG7QEQ'
EMAIL_HOST_PASSWORD = 'AlbxKXHApE81Dv2fU0/e8rLxv4JNAXCubbIgDVjSncq7'
EMAIL_USE_TLS = True

ACCESS_TOKEN_EXPIRE_SECONDS = 360000

# avatar
AVATAR_GRAVATAR_DEFAULT = 'mm'
AVATAR_AUTO_GENERATE_SIZES = (80, 250)

# haystack settings
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
        'URL': 'http://127.0.0.1:9200/',
        'INDEX_NAME': 'haystack',
    },
}

HAYSTACK_SEARCH_RESULTS_PER_PAGE = 20

HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'

# crontab settings
CRONJOBS = [
    ('0 0 * * *', 'sundog.cron.create_status_daily_stats')
]

# seed setting
SEED_FILE_ID = 1

# social login variables:
SOCIALACCOUNT_QUERY_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = 'none'
