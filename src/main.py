import certifi
from dotenv import dotenv_values
from pymongo import MongoClient
from fastapi import FastAPI
from fastapi import FastAPI
from src.database import MongoDatabase
from src.bikes.routers import router as bike_router
from src.auth.routers import router as auth_router
from src.notifications.routers import router as notification_router

app = FastAPI()

config = dotenv_values(".env")

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


app.include_router(bike_router)
app.include_router(auth_router)
app.include_router(notification_router)