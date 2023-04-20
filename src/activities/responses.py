from pydantic import BaseModel
from bikes.models import FoundBikeReport

from src.transfers.models import BikeTransfer


class ActivityResponse(BaseModel):
    alerts: int
    outgoing_transfer_requests: list[BikeTransfer]
    incoming_transfer_requests: list[BikeTransfer]
    completed_transfers: list[BikeTransfer]
    discoveries: list[FoundBikeReport]
    # Discoveries goes here
