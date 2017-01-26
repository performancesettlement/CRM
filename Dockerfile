FROM python:3.6

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y \
  gcc \
  gettext \
  postgresql-client libpq-dev \
  sqlite3 \
  --no-install-recommends && rm -rf /var/lib/apt/lists/*

ARG PIP_INDEX_URL
ARG PIP_TRUSTED_HOST
COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["./docker-entrypoint.sh"]

EXPOSE 80

CMD ["development"]

COPY local_config_docker.py local_config.py

COPY . /usr/src/app
