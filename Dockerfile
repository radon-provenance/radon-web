# Dockerfile
FROM python:3.11

ARG DSE_HOST
ARG MQTT_HOST

# Set environment variables 

# Hostnames for DSE (Cassandra) and MQTT
ENV DSE_HOST=${DSE_HOST}
ENV MQTT_HOST=${MQTT_HOST}

# Prevents Python from writing pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1

# Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1

ENV CQLENG_ALLOW_SCHEMA_MANAGEMENT=1

# Create destination folders
RUN mkdir -p /code/radon-lib && \
    mkdir -p /code/radon-web

# Install prerequisites
RUN apt -y update && \
    apt install -y nano less libldap2-dev libsasl2-dev libssl-dev && \
    pip install --upgrade pip && \
    apt clean

# Install radon-lib
COPY ./radon-lib /code/radon-lib
WORKDIR /code/radon-lib
RUN python -m pip install .

# Copy the requirements install Python dependencies
COPY ./radon-web/requirements.txt /code/radon-web
WORKDIR /code/radon-web
RUN pip install --no-cache-dir -r requirements.txt

# Install radon-web
COPY ./radon-web /code/radon-web
WORKDIR /code/radon-web
RUN python manage.py collectstatic --noinput
RUN python manage.py migrate --run-syncdb

# Expose the Django port
EXPOSE 8000

# For developmemt use Django's development server so it can track changes
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
# For production use Gunicorn 
#CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "project.wsgi:application"]
