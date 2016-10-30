import os
import local_config as local_config


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


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


INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'django.contrib.sites',
    'django_auth_app',
    'sundog',
    'rest_framework',
    'compressor',
    'taggit',
    'avatar',
    'colorful',
    'multi_email_field',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'crispy_forms',
    'datatableview',
    'django_bootstrap_breadcrumbs',
    'django_s3_storage',
    'fm',
    'multiselectfield',
    'tinymce',
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

    'sundog.middleware.ImpersonationMiddleware',
    'sundog.middleware.TimezoneMiddleware',

    'sundog.middleware.ExceptionResponderMiddleware',
)


ROOT_URLCONF = 'sundog.urls'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(PROJECT_ROOT, 'django_auth_app', 'templates'),
            os.path.join(
                PROJECT_ROOT,
                'django_auth_app/templates',
                'registration',
            ),
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
            'format':
                "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S",
        },

        'simple': {
            'format': '%(levelname)s %(message)s',
        },

    },

    'filters': {

        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },

    },

    'handlers': {

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
            'formatter': 'simple',
        },

        'logstash': {
            'level': 'DEBUG',
            'class': 'logstash.TCPLogstashHandler',
            'host': 'logstash',
            'port': '5000',
            'version': 1,
        },

    },

    'root': {
        'handlers': ['mail', 'syslog', 'logstash'],
        'level': 'DEBUG',
    },

    'loggers': {

        'root': {
            'handlers': ['logstash'],
            'level': 'DEBUG',
        },

        'sundog': {
            'handlers': ['mail', 'syslog', 'logstash'],
            'level': 'DEBUG',
        },

        'django_auth_app': {
            'handlers': ['mail', 'syslog', 'logstash'],
            'level': 'DEBUG',
        },

        'django': {
            'handlers': ['syslog', 'logstash'],
            'level': 'DEBUG',
        },

        'django.db.backends': {
            'handlers': ['syslog', 'logstash'],
            'level': 'DEBUG',
        },

        'django.request': {
            'handlers': ['syslog', 'mail', 'logstash'],
            'level': 'DEBUG',
        },

        'django.server': {
            'handlers': ['syslog', 'mail', 'logstash'],
            'level': 'DEBUG',
        },

        'gunicorn.access': {
            'handlers': ['syslog', 'mail', 'logstash'],
            'level': 'DEBUG',
        },

        'gunicorn.error': {
            'handlers': ['syslog', 'mail', 'logstash'],
            'level': 'DEBUG',
        },

    },
}


LANGUAGE_CODE = 'en'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'
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

# seed setting
SEED_FILE_ID = 1

SHORT_DATETIME_FORMAT = 'm/d/Y h:i a'

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files storage in Amazon S3:
DEFAULT_FILE_STORAGE = 'django_s3_storage.storage.S3Storage'
AWS_S3_CALLING_FORMAT = 'boto.s3.connection.SubdomainCallingFormat'
AWS_S3_HOST = 's3-us-west-2.amazonaws.com'
AWS_S3_BUCKET_NAME = (
    'performance-settlement-crm-media-dev'
    if DEBUG
    else 'performance-settlement-crm-media'
)
S3_URL = 'https://%s.s3.amazonaws.com' % AWS_S3_BUCKET_NAME
MEDIA_DIRECTORY = '/media/'
MEDIA_URL = S3_URL + MEDIA_DIRECTORY
MEDIA_PUBLIC = MEDIA_DIRECTORY + 'public/'
MEDIA_PRIVATE = MEDIA_DIRECTORY + 'private/'

BREADCRUMBS_TEMPLATE = 'django_bootstrap_breadcrumbs/bootstrap3.html'

CRISPY_TEMPLATE_PACK = 'bootstrap3'


TINYMCE_BASE_URL = 'https://cdnjs.cloudflare.com/ajax/libs/tinymce/4.4.3'
TINYMCE_JS_URL = TINYMCE_BASE_URL + '/tinymce.min.js'

TINYMCE_SPELLCHECKER = True

TINYMCE_PLUGINS = {
    'advlist',
    'anchor',
    'autolink',
    'autoresize',
    'autosave',
    'charmap',
    'code',
    'codesample',
    'colorpicker',
    'contextmenu',
    'directionality',
    'emoticons',
    'fullpage',
    'fullscreen',
    'hr',
    'image',
    'imagetools',
    'importcss',
    'insertdatetime',
    'layer',
    'legacyoutput',
    'link',
    'lists',
    'media',
    'nonbreaking',
    'noneditable',
    'pagebreak',
    'paste',
    'preview',
    'print',
    'save',
    'searchreplace',
    'spellchecker',
    'tabfocus',
    'table',
    'template',
    'textcolor',
    'textpattern',
    'visualblocks',
    'visualchars',
    'wordcount',
}

TINYMCE_DEFAULT_CONFIG = {
    'cleanup_on_startup': True,
    'custom_undo_redo_levels': 10,
    'external_plugins': {
        plugin: '{base}/plugins/{plugin}/plugin.min.js'.format(
            base=TINYMCE_BASE_URL,
            plugin=plugin,
        )
        for plugin in TINYMCE_PLUGINS
    },
    'plugins': ','.join(TINYMCE_PLUGINS),
    'setup': 'tinymce_setup',
    'theme': 'modern',
    'toolbar': [
        ','.join(row)
        for row in [

            [
                'styleselect',
                'formatselect',
                'fontselect',
                'fontsizeselect',
            ],

            [
                'newdocument'
                '|',
                'undo',
                'redo',
                '|',
                'bold',
                'italic',
                'underline',
                'strikethrough',
                'subscript',
                'superscript',
                'removeformat',
                '|',
                'alignleft',
                'aligncenter',
                'alignright',
                'alignjustify',
                'alignnone',
            ],

            [
                'cut',
                'copy',
                'paste',
                'pastetext',
                '|',
                'searchreplace',
                '|',
                'bullist',
                'numlist',
                '|',
                'outdent',
                'indent',
                'blockquote',
                '|',
                'link',
                'unlink',
                'anchor',
                'image',
                'code',
            ],

            [
                'insertdatetime',
                'preview',
                '|',
                'forecolor',
                'backcolor',
                '|',
                'hr',
                '|',
                'charmap',
                'media',
                '|',
                'print',
                '|',
                'ltr',
                'rtl',
                '|',
                'fullscreen',
                '|',
                'spellchecker',
                '|',
                'pagebreak',
            ],

        ]
    ],
}
