



# Build Docker image
cd ..
docker build -t radon-web-image .


# run image


docker run --rm --name radon-web -p 8000:8000 -ti radon-web-image:latest python manage.py runserver 0.0.0.0:8000


docker run --rm --name radon-web -p 8000:8000 -ti radon-web-image:latest /bin/bash



docker run --rm --name radon-web -p 8000:8000 -v radon-lib:/code/radon-lib -ti radon-web-image:latest /bin/bash
