from fastapi import FastAPI
from src.database import MongoDatabase
from src.routers import main_router

from src.settings import app

@app.on_event("startup")
def startup_db_client():
    mongo_db = MongoDatabase()
    mongo_db.connect()

    # By setting the client on the app its possible to get the connection
    # from any request inside routers
    app.mongodb_client = mongo_db.connection
    app.collections = mongo_db.collections

@app.on_event("shutdown")
def shutdown_db_client():
    app.mongodb_client.close()

app.include_router(main_router)