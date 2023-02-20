import datetime
from enum import Enum
import uuid
from pydantic import BaseModel, Field

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


class BikeOwner(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, alias="_id")
    phone_number: str = "" # TODO: Maybe hash this at some point to avoid possible leakage
    verified: bool = False
    created_at: datetime.datetime = datetime.datetime.now()
    

class Bike(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, alias="_id")
    frame_number: str = Field(...)
    owner: BikeOwner
    gender: BikeGender | None = None
    is_electic: bool = False
    kind: BikeKind | None = None
    brand: str = "" # Should be a model
    color: BikeColor | None = None
    images: str = "" # Should be its own model or something else
    receipt: str = "" # Same as images
    reported_stolen: bool = False
    claim_token: uuid.UUID = Field(default_factory=uuid.uuid4, alias="_id")
    claimed_date: datetime.datetime = datetime.datetime.now()
    stolen_date: datetime.datetime = datetime.datetime.now()
    created_at: datetime.datetime = datetime.datetime.now()
    state: BikeState | None = None # Figure out how to handle states
    
    class Config:  
        use_enum_values = False
    
    