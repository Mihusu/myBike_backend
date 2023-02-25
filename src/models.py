from typing import Self
import uuid
from pydantic import BaseModel, Field, PrivateAttr

from src.database import MongoDatabase


class Entity(BaseModel):
    """ 
    Serves as a base class for all entities within the application
    mainly to group common behavior in a single class.
    """

    _COLLECTION_NAME : str | None = PrivateAttr(default=None)      # Name of the mongodb collection this entity should be saved to

    id: uuid.UUID = Field(default_factory=uuid.uuid4, alias="_id")


    def save(self) -> Self:
        """
        Save the model as a document in mongodb

        :returns the updated instance after saving to the database
        """
        db = MongoDatabase()

        if self._COLLECTION_NAME is None:
            raise NotImplementedError(f"model '{self.__class__.__name__}' is missing a collection name. *Hint set the COLLECTION_NAME attribute on the model")
        
        # Make an update or insert on the instance
        db.collections[self._COLLECTION_NAME].update_one({'_id' : self.id}, {'$set' : self.dict()}, upsert=True)

        doc = db.collections[self._COLLECTION_NAME].find_one({'_id' : self.id})
        return self.__class__(**doc)