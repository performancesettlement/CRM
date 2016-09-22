#!/bin/bash
set -e

python manage.py makemigrations
yes yes | python manage.py migrate

if [[ "${1}" = 'development' ]]; then
    echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'admin')" | python manage.py shell || true
fi

exec gunicorn --config='conf/gunicorn.py' sundog.wsgi
