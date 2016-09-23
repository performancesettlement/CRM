#!/usr/bin/env bash

ln -s docker-compose.production.yml docker-compose.override.yml
echo "SECRET_KEY='$(cat /proc/sys/kernel/random/uuid)'" >> .env
