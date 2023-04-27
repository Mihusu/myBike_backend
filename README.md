# MinCykel Backend

## 1. Install and running project


### 1.1 Setup virtual environment

Make a virtual environment to isolate the project from your globally installed
python packages.

(*Note) It's only required to create an environment once on first git clone

Unix/macOs
```console
python3 -m venv env
```
Windows
```
py -m venv env
```

Then activate the virtual environment:

Unix/macOs
```
source env/bin/activate
```
Windows
```
.\env\Scripts\activate
```

To deactivate the environment use:
```
deactivate
```
### 1.2 Install requirements

```
pip install -r requirements.txt
```

### 1.3 Running the server

To run the project from terminal, use the following command:
```
uvicorn src.main:app --reload
```

Alternatively, if inside vscode editor, simply run the project by using the "Run and Debug" on 
the sidepanel

## 2. Development 

### 2.1 Python version 3.11 - Mandatory

It is mandatory to install Python version 3.11 or above to get accurate type-hints while developing

### 2.2 Commit policy

Commit code to the development branch

# Docker deployment

### Step 1. Create and upload docker image

First, build the image with the following command:
```console
docker build -t jsaad20/production:latest .
```

This will create a docker image.
Next we push this image to docker hub so we can later pull down the image
from claaudia.
```console
docker push jsaad20/production:latest
```

### Step 2. Login and pull docker image from claaudia server
```console
$ sudo docker pull jsaad20/production:latest
```

If the container have not been started on the server (it should always be running), it can be started with the following command:
```console
sudo docker-compose -f docker-compose.yml up -d
```

To run traefik run:
```console
sudo docker-compose -f docker-compose.traefik.yml up -d
```

Now we use docker run with watchtower to startup the application
while watchtower listens for updates to the base image to automatically apply changes
```console
sudo docker run -ti -d \
  --name watchtower \
  -e REPO_USER=jsaad20 \
  -e REPO_PASS=weZcom-jenve0-pozpyr \
  -v /var/run/docker.sock:/var/run/docker.sock \
  containrrr/watchtower backend.prod --interval 30
```


