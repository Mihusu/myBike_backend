# MinCykel Backend

## 1. Install and running project

### 1.1 Setup virtual environment

To have all the dependencies used in the project, create a virtual environment with the following command:

Unix/macOs
```console
python3 -m venv env  (Only first time setup)
```
Windows
```
py -m venv env  (Only first time setup)
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

### 1.3 Running the server from terminal

```
uvicorn main:app --reload
```

## 2. Development

Commit code to the development branch

