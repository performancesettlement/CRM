#!/bin/bash
set -e

python manage.py makemigrations
yes yes | python manage.py migrate

case "${1}" in
  ('development')
    echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'admin')" | python manage.py shell || true
  ;;
  ('production')
    python manage.py collectstatic --noinput || true
  ;;
esac

exec gunicorn --config='conf/gunicorn.py' sundog.wsgi
