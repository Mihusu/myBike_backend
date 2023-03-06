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

