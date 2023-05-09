# MinCykel Backend

This is the backend application for mincykelapp.dk.

It can be found deployed at: https://api.mincykelapp.dk

Logo hopefully comming soon ...

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

# Deployment to production

## Prerequisites

* Have docker installed
* Logged into docker with docker login

The login credentials for docker can be found on the discord server

### Step 1. Build and push the docker image

First, build the image with the following command:
```console
docker build -t jsaad20/production:backend .
```

Next we push this image to docker hub
from claaudia.
```console
docker push jsaad20/production:backend
```

### Thats it 🚀

The server is setup to automatically listen to new image pushes so everything should be updated on the server


# Advanced server notes
### Login and pull docker image from claaudia server

Ssh into the backend server with the following command:
```console
$ sudo ssh ubuntu@130.225.39.185 -i secret.pem 
```
secret.pem file can be found on discord server

Pull down the image from docker hub
```console
$ sudo docker pull jsaad20/production:backend
```

If the container have not been started on the server (it should always be running), it can be started with the following command:
```console
sudo docker-compose -f docker-compose.backend.yml up -d
```

To run traefik run:
```console
sudo docker-compose -f docker-compose.traefik.yml up -d
```


