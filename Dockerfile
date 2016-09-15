FROM django:onbuild

COPY local_config_docker.py local_config.py
COPY conf/ conf/
RUN mkdir -p log && touch log/django.log log/sundog.log
RUN python manage.py makemigrations

CMD \
  python manage.py migrate && \
  echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'admin')" | python manage.py shell && \
  gunicorn --config='conf/gunicorn.py' sundog.wsgi
