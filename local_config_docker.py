from os import environ

# Apparently unused options for django.contrib.sites:
SITE_DOMAIN = ''
SITE_HOST = ''
HOST = environ.get('HOST', 'localhost')

# Disabled if running in debugging mode; this is probably not important for now:
ALLOWED_HOSTS = []

DEBUG = environ.get('DEBUG', 'True') == 'True'

# Secrets:
ADDRESS_API_KEY = ''
SECRET_KEY = environ.get('SECRET_KEY', 'xyzzy')

# Database connection setup:
DATABASE_HOST = 'postgres'
DATABASE_PORT = '5432'
DATABASE_NAME = 'sundog_db'
DATABASE_USER = 'sundog_db'
DATABASE_PASSWORD = 'sundog_db'
