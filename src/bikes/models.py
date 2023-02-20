import datetime
from enum import Enum
import uuid
from pydantic import BaseModel, Field

class BikeGender(str, Enum):
    MALE = 0,
    FEMALE = 1,
    UNI_SEX = 2


class BikeKind(str, Enum):
    CITY = 0,
    MOUNTAIN = 1,
    ROAD = 2,
    RACE = 3,
    CARGO = 4,
    HYBRID = 5,
    CRUISER = 6,
    FOLDING = 7,
    BMX = 8,
    OTHER = 9


class BikeColor(str, Enum):
    BLACK = 0,
    WHITE = 1,
    GRAY = 2,
    RED = 3,
    BLUE = 4,
    GREEN = 5,
    YELLOW = 6,
    ORANGE = 7,
    PURPLE = 8,
    OTHER = 9


class BikeOwner(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, alias="_id")
    phone_number: str = ""
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
    state: str = "" # Figure out how to handle states
    
    class Config:  
        use_enum_values = False
    
    