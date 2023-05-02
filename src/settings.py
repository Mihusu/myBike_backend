import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import dotenv_values

class Bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

config = dotenv_values(".env.local")
app = FastAPI()


if os.getenv('ENV') == 'prod':
    print(f"{Bcolors.OKBLUE}[Env]:{Bcolors.ENDC}    production")
    config = dotenv_values(".env.prod")
    app = FastAPI(
        docs_url=None, # Disables /docs
        redoc_url=None # Disables /redoc
    )
else:
    print(f"{Bcolors.OKBLUE}[Env]:{Bcolors.ENDC}    local")
    config = dotenv_values(".env.local")
    app = FastAPI()


origins = [
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
    "http://mincykelapp.dk",
    "https://mincykelapp.dk",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)