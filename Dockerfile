# Dockerfile
FROM python:3.11

# Hostnames for dse and mqtt servers
ARG DSE_HOST
ARG MQTT_HOST

ENV PYTHONUNBUFFERED 1
ENV DSE_HOST=${DSE_HOST}
ENV MQTT_HOST=${MQTT_HOST}
ENV CQLENG_ALLOW_SCHEMA_MANAGEMENT 1

# Install prerequisites
RUN apt -y update && \
    apt install -y nano less libldap2-dev libsasl2-dev libssl-dev && \
    pip install --upgrade pip && \
    apt clean

# Create destination folders
RUN mkdir -p /code/radon-lib && \
    mkdir -p /code/radon-web

# Install radon-lib
COPY radon-lib /code/radon-lib
WORKDIR /code/radon-lib
RUN pip install -r requirements.txt
RUN python setup.py develop

# Install radon-web
COPY radon-web /code/radon-web
WORKDIR /code/radon-web
RUN pip install -r requirements.txt
RUN python manage.py collectstatic --noinput
RUN python manage.py migrate --run-syncdb
