import datetime
from pydantic import PrivateAttr

from src.models import Entity
from src.auth.models import DeviceList


class BikeOwner(Entity):
    
    _COLLECTION_NAME = PrivateAttr(default='bike_owners')
    
    phone_number: str   # TODO: Maybe hash this at some point to avoid possible leakage
    hash: bytes
    created_at: datetime.datetime = datetime.datetime.now()
    devices: DeviceList = DeviceList()