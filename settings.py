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

SITE_DOMAIN = local_config.SITE_DOMAIN
ALLOWED_HOSTS = local_config.ALLOWED_HOSTS
SITE_HOST = local_config.HOST
DEBUG = local_config.DEBUG
SECRET_KEY = local_config.SECRET_KEY
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
    'colorful',
    'multi_email_field',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'datatableview',
)

MIDDLEWARE_CLASSES = (
    'htmlmin.middleware.HtmlMinifyMiddleware',
    'htmlmin.middleware.MarkRequestMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',

    'whitenoise.middleware.WhiteNoiseMiddleware',

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
                'django.template.context_processors.i18n',
                'django.template.context_processors.debug',
                'django.template.context_processors.media',
                'django.template.context_processors.csrf',
                'django.template.context_processors.tz',
                'django.template.context_processors.static',
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
    'disable_existing_loggers': False,
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
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
        'logstash': {
            'level': 'DEBUG',
            'class': 'logstash.TCPLogstashHandler',
            'host': 'logstash',
            'port': 5000,
            'version': 1,
        },
    },
    'root': {
        'handlers': ['info_file', 'mail', 'syslog', 'console', 'logstash'],
        'level': 'DEBUG',
    },
    'loggers': {
        'root': {
            'handlers': ['console', 'logstash'],
            'level': 'DEBUG',
        },
        'sundog': {
            'handlers': ['info_file', 'mail', 'syslog', 'console', 'logstash'],
            'level': 'DEBUG',
        },
        'django_auth_app': {
            'handlers': ['info_file', 'mail', 'syslog', 'console', 'logstash'],
            'level': 'DEBUG',
        },
        'django': {
            'handlers': ['syslog', 'django', 'console', 'logstash'],
            'level': 'DEBUG',
        },
        'django.db.backends': {
            'handlers': ['syslog', 'django', 'console', 'logstash'],
            'level': 'DEBUG',
        },
        'django.request': {
            'handlers': ['syslog', 'mail', 'django', 'console', 'logstash'],
            'level': 'DEBUG',
        },
        'django.server': {
            'handlers': ['syslog', 'mail', 'django', 'console', 'logstash'],
            'level': 'DEBUG',
        },
        'gunicorn.access': {
            'handlers': ['syslog', 'mail', 'django', 'console', 'logstash'],
            'level': 'DEBUG',
        },
        'gunicorn.error': {
            'handlers': ['syslog', 'mail', 'django', 'console', 'logstash'],
            'level': 'DEBUG',
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

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
NO_REPLY_EMAIL_ADDRESS = "info@performancesettlement.com"
# INFO_EMAIL_ADDRESS = "careers@mahisoft.com"
# TO_CONTACT_INFO_EMAIL_ADDRESS = "careers@mahisoft.com"

EMAIL_HOST = 'smtp.coxmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'psettelment@printer.occoxmail.com'
EMAIL_HOST_PASSWORD = 'summer2016'
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

SHORT_DATETIME_FORMAT = 'm/d/Y h:i a'

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
