#!/bin/bash
set -e

touch sundog/migrations/__init__.py
python manage.py makemigrations
yes yes | python manage.py migrate

case "${1}" in
  ('development')
    # Development profile setup goes here:
    true
  ;;
  ('production')
    python manage.py collectstatic --noinput || true
  ;;
esac

exec gunicorn --config='conf/gunicorn.py' sundog.wsgi
