import certifi
from dotenv import dotenv_values
from fastapi import FastAPI
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.database import MongoDatabase
from src.routers import main_router

config = dotenv_values(".env")

if config['ENVIRONMENT'] == 'prod':
    app = FastAPI(
        docs_url=None, # Disables /docs
        redoc_url=None # Disables /redoc
    )
elif config['ENVIRONMENT'] == 'dev':
    app = FastAPI()
else:
    print("Unknown Environment!")
    exit()


origins = [
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://localhost:5173",
    "http://localhost:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_db_client():
    print("Setting up database...")
    
    mongo_db = MongoDatabase()
    mongo_db.connect()

    # By setting the client on the app its possible to get the connection
    # from any request inside routers
    app.mongodb_client = mongo_db.connection
    app.collections = mongo_db.collections

@app.on_event("shutdown")
def shutdown_db_client():
    print("Closing database...")
    app.mongodb_client.close()

app.include_router(main_router)