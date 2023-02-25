import datetime
from enum import Enum
import uuid
from fastapi import Form
from pydantic import BaseModel, Field, PrivateAttr, validator
import re as regex

from src.models import Entity

class BikeGender(str, Enum):
    MALE = "male",
    FEMALE = "female",
    UNI_SEX = "uni_sex"


class BikeKind(str, Enum):
    CITY = "city",
    MOUNTAIN = "mountain",
    ROAD = "road",
    RACE = "race",
    CARGO = "cargo",
    HYBRID = "hybrid",
    CRUISER = "cruiser",
    FOLDING = "folding",
    BMX = "bmx",
    OTHER = "other"


class BikeColor(str, Enum):
    BLACK = "black",
    WHITE = "white",
    GRAY = "gray",
    RED = "red",
    BLUE = "blue",
    GREEN = "green",
    YELLOW = "yellow",
    ORANGE = "orange",
    PURPLE = "purple",
    OTHER = "other"


class BikeState(str, Enum):
    UNCLAIMED = "unclaimed",
    CLAIMED = "claimed",
    REPORTED_STOLEN = "reported_stolen"


class BikeOwnerCredentials(BaseModel):
    phone_number: str = ""
    password: str = ""
    
    
class BikeOwner(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, alias="_id")
    phone_number: str = "" # TODO: Maybe hash this at some point to avoid possible leakage
    verified: bool = False
    created_at: datetime.datetime = datetime.datetime.now()
    

class Bike(Entity):

    _COLLECTION_NAME = PrivateAttr(default='bikes')

    frame_number: str = Field(...)
    owner: BikeOwner | None = None
    gender: BikeGender
    is_electic: bool
    kind: BikeKind
    brand: str # Should be a model
    color: BikeColor
    images: list[str] | None # Should be its own model or something else
    receipt: list[str] | None # Same as images
    reported_stolen: bool = False
    claim_token: uuid.UUID = Field(default_factory=uuid.uuid4)
    claimed_date: datetime.datetime | None
    stolen_date: datetime.datetime | None
    created_at: datetime.datetime = datetime.datetime.now()
    state: BikeState = BikeState.UNCLAIMED # Figure out how to handle these states
    
    @validator('frame_number')
    def validate_frame_number(cls, value):
        """ Validates the frame number according to the danish frame number format

        MANUFACTUER_NUMBER | SERIAL_NUMBER | YEAR_MARK

        MANUFACTUER_NUMBER  : 1..4 characters
        SERIAL_NUMBER       : 1..* characters
        YEAR_MARK           : 1 character

        @See: https://da.wikipedia.org/wiki/Det_danske_stelnummersystem_for_cykler for more info
        """
        valid = regex.search("^[a-zA-Z]{1,4}[0-9]+[a-zA-Z]$", value)
        if valid:
            return value
        else:
            raise ValueError(f"Invalid frame number. See https://da.wikipedia.org/wiki/Det_danske_stelnummersystem_for_cykler for valid frame numbers")


class BikeRegistrationInfo(BaseModel):
    frame_number: str = Form(...)
    gender: BikeGender = Form(...)
    is_electic: bool = Form(...)
    kind: BikeKind = Form(...)
    brand: str = Form(...)
    color: BikeColor = Form(...)
    

# ___ Changelog ___
# TODO: Add testing framework