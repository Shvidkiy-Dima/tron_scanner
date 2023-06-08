
FROM python:3.9-slim-buster

ENV PYTHONUNBUFFERED 1

RUN apt-get update \
  # dependencies for building Python packages
  && apt-get install -y build-essential \
  # psycopg2 dependencies
  && apt-get install -y libpq-dev \
  # Translations dependencies
  && apt-get install -y gettext \
  # cleaning up unused files
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

# Requirements are installed here to ensure they will be cached.
COPY ./requirements /requirements

RUN  pip3 install --upgrade pip
RUN pip install --no-cache-dir -r /requirements/base.txt && rm -rf /requirements


COPY . /app
WORKDIR /app

COPY ./start.sh /start.sh
COPY ./check_conn.py /app/check_conn.py

RUN chmod +x /start.sh
