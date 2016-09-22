FROM python:3.5

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y \
  gcc \
  gettext \
  postgresql-client libpq-dev \
  sqlite3 \
  --no-install-recommends && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /usr/src/app
COPY local_config_docker.py local_config.py
RUN mkdir -p log && touch log/django.log log/sundog.log

COPY docker-entrypoint.sh .

ENTRYPOINT ["docker-entrypoint.sh"]

EXPOSE 80

CMD ["development"]
