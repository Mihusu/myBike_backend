import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import dotenv_values
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration


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
    
    
#if os.getenv('ENV') == 'prod':
if True:
    print(f"{Bcolors.OKBLUE}[Log]:{Bcolors.ENDC}    production")
    # All of this is already happening by default!
    sentry_logging = LoggingIntegration(
        level=logging.INFO,        
        event_level=logging.WARNING   
    )

    sentry_sdk.init(
        dsn="https://2564cb71cf79471588d58b6c5e368093@o4505115189772288.ingest.sentry.io/4505115191476224",
        environment="production",
        
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production,
        traces_sample_rate=1.0,
        integrations=[
            sentry_logging
        ]
    )
else:
    print(f"{Bcolors.OKBLUE}[Log]:{Bcolors.ENDC}    local")



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
    "http://127.0.0.1",
    "http://localhost",
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
    allow_origin_regex="http[s]?://172.25.0.3:[0-9]{1,5}",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)