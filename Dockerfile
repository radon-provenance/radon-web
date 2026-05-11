# Build
FROM python:3.11-slim AS builder


RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libldap2-dev libsasl2-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt


# Runtime
FROM python:3.11-slim

# System dependencies for runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libldap2 libsasl2-2 libssl3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY . .

RUN chmod +x /app/entrypoint.sh

# Variable de version
ARG APP_VERSION=0.0.0
ENV APP_VERSION=$APP_VERSION

ENTRYPOINT ["/app/entrypoint.sh"]

# Default command (gunicorn for production)
CMD ["gunicorn", "project.wsgi:application", "--bind", "0.0.0.0:8000"]


# ------ OLD DOCKERFILE CONTENT BELOW ------

# Hostnames for dse and mqtt servers
#ARG DSE_HOST
#ARG MQTT_HOST

#ENV PYTHONUNBUFFERED=1
#ENV DSE_HOST=${DSE_HOST}
#ENV MQTT_HOST=${MQTT_HOST}
#ENV CQLENG_ALLOW_SCHEMA_MANAGEMENT=1

# Install prerequisites
#RUN apt -y update && \
#    apt install -y nano less libldap2-dev libsasl2-dev libssl-dev && \
#    pip install --upgrade pip && \
#    apt clean

# Create destination folders
#RUN mkdir -p /code/radon-web

# Install radon-web
#COPY . /code/radon-web
#WORKDIR /code/radon-web
#RUN pip install -r requirements.txt
#RUN python manage.py collectstatic --noinput
#RUN python manage.py migrate --run-syncdb
