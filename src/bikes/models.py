import datetime
import uuid
from enum import Enum
from pydantic import Field, PrivateAttr

from src.models import Entity
from src.storage.models import S3File

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

    
class BikeOwner(Entity):
    
    _COLLECTION_NAME = PrivateAttr(default='bike_owners')
    
    phone_number: str   # TODO: Maybe hash this at some point to avoid possible leakage
    hash: bytes
    created_at: datetime.datetime = datetime.datetime.now()
    

class Bike(Entity):

    _COLLECTION_NAME = PrivateAttr(default='bikes')

    frame_number: str
    owner: uuid.UUID | None = None
    gender: BikeGender
    is_electric: bool
    kind: BikeKind
    brand: str                          # Should probably be a model but is fine for now
    color: BikeColor
    image: S3File | None = S3File.field(path='bike-images', allowed_content_types=['image/png', 'image/jpeg', 'image/jpg'])
    receipt: S3File | None = S3File.field(path='bike-receipts', allowed_content_types=['*'])
    reported_stolen: bool = False
    claim_token: uuid.UUID = Field(default_factory=uuid.uuid4)
    claimed_date: datetime.datetime | None
    stolen_date: datetime.datetime | None
    created_at: datetime.datetime = datetime.datetime.now()
    state: BikeState = BikeState.UNCLAIMED      # Simple state variable is fine for now. Maybe in the future, more structure to the state could be needed
    
# ___ Changelog ___
# TODO: Add testing framework
# TODO: Wrap up S3Files