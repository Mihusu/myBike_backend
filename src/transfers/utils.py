from fastapi import Request

from src.bikes.models import Bike, BikeOwner
from src.transfers.models import BikeTransfer


def expand_transfer(transfer: BikeTransfer, request: Request) -> dict:
    """ Serializes a single bike transfer to expand ids into full objects """
    
    sender   = BikeOwner(**request.app.collections['bike_owners'].find_one({'_id' : transfer.sender})).dict(include={'_id', 'phone_number'})
    reciever = BikeOwner(**request.app.collections['bike_owners'].find_one({'_id' : transfer.receiver})).dict(include={'_id', 'phone_number'})
    bike     = Bike(**request.app.collections['bikes'].find_one({'_id' : transfer.bike_id})).dict(exclude={'receipt'})
    
    return {
        'sender'     : sender,
        'receiver'   : reciever,
        'bike'       : bike,
        'created_at' : transfer.created_at,
        'closed_at'  : transfer.closed_at,
        'state'      : transfer.state
    }