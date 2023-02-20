from dotenv import dotenv_values
from pymongo import MongoClient
from fastapi import FastAPI
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

import certifi

from src.bikes.routers import router as bike_router
from src.auth.routers import router as auth_router

app = FastAPI()

config = dotenv_values(".env")

@app.on_event("startup")
def startup_db_client():
    print("Setting up database...")
    
    # For some reason, the database connection fails with SSL: CERTIFICATE_VERIFY_FAILED
    # when not using tlsCAFile=certifi.where(), so i am keeping it here for now until 
    # a new solution is found.
    app.mongodb_client = MongoClient(config["ATLAS_URI"], tlsCAFile=certifi.where())
    app.database = app.mongodb_client[config["DB_NAME"]]

@app.on_event("shutdown")
def shutdown_db_client():
    print("Closing database...")
    app.mongodb_client.close()


app.include_router(bike_router)
app.include_router(auth_router)