# Radon Web server


## Presentation

The Web Interface is run as a Docker image on several nodes of the Radon 
cluster. It is powered by Django/Gunicorn and provides a simple interface to the 
Data Management System via a Web browser.

All the CRUD functions are available through the interface and it displays the 
hierarchy of the data objects/collections created in the system.

It requires the radon-lib library to work to access the data stored in the 
Cassandra database.
In order to work correctly it requires a running radon-listener to fire the rules.


## Version

The current version is 1.1.0


## Install and test the web server for development


### Create its own virtual environment

```
python3 -m venv ~/ve/radon-web
source ~/ve/radon-web/bin/activate
```

### Install Radon-lib

```
cd ... /radon-lib/
pip install -r requirements.txt
python setup.py develop
```

### Install Radon-web

```
cd ... /radon-web/
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --run-syncdb
```

### Run Radon-web

```
./start.sh
```

## Install with the docker image


###  Build Docker image

```
cd ..
export DSE_HOST="`docker exec dse hostname -i`"
export MQTT_HOST="`docker exec mqtt hostname -i`"
docker build -t radon-web-image \
             --build-arg DSE_HOST=${DSE_HOST} \
             --build-arg MQTT_HOST=${MQTT_HOST} \
             -f radon-web/Dockerfile .
```

### Run image

```
docker run --name radon-web \
           -p 8000:8000 \
           -d radon-web-image:latest \
           gunicorn project.wsgi:application --bind 0.0.0.0:8000 \
           --workers 10 --threads 10 --worker-tmp-dir /dev/shm
```


### Develop with the image

```
docker run --rm --name radon-web \
           -p 8000:8000 -v radon-lib:/code/radon-lib \
           -ti radon-web-image:latest /bin/bash
```


# License

Licensed under the Apache License, Version 2.0 (the "License"); 
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed
under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR 
CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and limitations under the License.


Parts of this work were supported by the Software Sustainability Institute with 
funding from EPSRC, BBSRC, ESRC, NERC, AHRC, STFC and MRC through grant EP/S021779/1.
