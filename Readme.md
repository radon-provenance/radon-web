# Test the web server

python3 -m venv ~/ve/radon-web
source ~/ve/radon-web/bin/activate
pip install -r requirements.txt


# Build Docker image
cd ..
docker build -t radon-web-image .


# run image


docker run --rm --name radon-web -p 8000:8000 -ti radon-web-image:latest python manage.py runserver 0.0.0.0:8000


docker run --rm --name radon-web -p 8000:8000 -ti radon-web-image:latest /bin/bash



docker run --rm --name radon-web -p 8000:8000 -v radon-lib:/code/radon-lib -ti radon-web-image:latest /bin/bash



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
