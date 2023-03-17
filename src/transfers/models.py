import datetime
from enum import Enum
import uuid
from fastapi import Form
from pydantic import BaseModel, Field, PrivateAttr, validator
import re as regex

from src.models import Entity

class TransferState(str, Enum):
    PENDING = "pending",
    CLOSED = "closed"

class Transfer(Entity):

    _COLLECTION_NAME = PrivateAttr(default='transfers')

    sender: str
    receiver: str
    bikeId: str
    created_at: datetime.datetime = datetime.datetime.now()
    state: TransferState.PENDING
