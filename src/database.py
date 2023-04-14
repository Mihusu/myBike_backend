import certifi
from dotenv import dotenv_values
from pymongo import MongoClient
from typing import Collection


config = dotenv_values(".env")


class MongoDatabase:

    connection      : MongoClient
    collections     : Collection

    def connect(self):
        """Opens a connection to the mongo database"""

        # Setting the client connection as a class variable makes all subsequent instanciations
        # of the MongoDatabase class able to see connection
        __class__.connection = MongoClient(config["ATLAS_URI"], tlsCAFile=certifi.where(), uuidRepresentation='standard')
        __class__.collections = __class__.connection[config["DB_NAME"]]


    def disconnect(self):
        """Closes the connection to the mongo database"""
        if __class__.connection:
            __class__.connection.close()
        