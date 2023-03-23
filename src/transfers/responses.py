from pydantic import BaseModel

from src.transfers.models import BikeTransfer


class ActivityResponse(BaseModel):
    outgoing_transfer_requests  : list[BikeTransfer]
    incomming_transfer_requests : list[BikeTransfer]
    completed_transfers         : list[BikeTransfer]
    #Discoveries goes here