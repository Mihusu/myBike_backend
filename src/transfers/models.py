import datetime
from enum import Enum
import uuid
from fastapi import Form
from pydantic import BaseModel, Field, PrivateAttr, validator
import re as regex

from src.models import Entity


class BikeTransferState(str, Enum):
    PENDING = "pending",
    ACCEPTED = "accepted",
    DECLINED = "declined"

class BikeTransfer(Entity):

    _COLLECTION_NAME = PrivateAttr(default='transfers')

    sender: uuid.UUID
    receiver: uuid.UUID
    bike_id: uuid.UUID
    created_at: datetime.datetime = datetime.datetime.now()
    closed_at: datetime.datetime = None
    state: BikeTransferState = BikeTransferState.PENDING
