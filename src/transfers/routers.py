import uuid
import datetime
from fastapi import APIRouter, Body, Depends, Form, Request, Response, HTTPException, UploadFile, File, status
from src.bikes.models import Bike, BikeOwner, BikeState
from src.auth.dependencies import authenticated_request
from src.notifications.sms import send_sms
from src.storage.aws import save_file
from src.transfers.models import BikeTransfer, BikeTransferState
from src.transfers.dependencies import bike_with_id_exists, transfer_with_id_exists

router = APIRouter(
    tags=['transfers'],
    prefix='/transfers'
)

@router.post('/', description="creating a bike transfer", status_code=status.HTTP_201_CREATED)
def create_transfer(
    request: Request, 
    sender: BikeOwner = Depends(authenticated_request), 
    receiver_phone_number = Body(), 
    bike_id: uuid.UUID = Depends(bike_with_id_exists)
) -> BikeTransfer:
    
    #check receiver exists
    receiver_in_db = request.app.collections["bike_owners"].find_one({"phone_number": receiver_phone_number})
    if not receiver_in_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Bike owner with phone number {receiver_phone_number} not found")
    
    #check bike exists
    #done in dependencies

    #check sender owns bike
    bike_owner = request.app.collections["bikes"].find_one({"owner": sender.id})
    if not bike_owner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Bike owner with phone number {sender.phone_number} does not own bike with id {bike_id}")
    
    #check bike not stolen
    bike_in_db = request.app.collections["bikes"].find_one({"_id": bike_id})
    bike = Bike(**bike_in_db)
    if bike.reported_stolen:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Bike is reported stolen. Transfer disallowed")
    
    #check bike not in transfer
    if bike.state == BikeState.IN_TRANSFER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Bike is already in transfer")
    
    #Make a transfer object
    transfer_info = {
        'sender': sender.id, 
        'receiver': receiver_in_db["_id"],
        'bike_id': bike_id,
        
    }

    transfer = BikeTransfer(**transfer_info)
    bike.state = BikeState.IN_TRANSFER

    #return transfer object to request sender
    return transfer.save() and bike.save()


@router.post('/{:id}/accept', description="Accepts a bike transfer", status_code=status.HTTP_202_ACCEPTED)
def accept_transfer(
    request: Request, 
    sender: BikeOwner = Depends(authenticated_request), 
    bike_id: uuid.UUID = Depends(bike_with_id_exists),
    transfer_id: uuid.UUID = Depends(transfer_with_id_exists)
) -> BikeTransfer:
         
    # Checks the bike is not stolen
    bike_in_db = request.app.collections["bikes"].find_one({"_id": bike_id})
    bike = Bike(**bike_in_db)
    if bike.reported_stolen:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Bike is reported stolen. Transfer disallowed")

    # Checks the transfer exists and not closed
    transfer_in_db = request.app.collections["transfers"].find_one({"_id": transfer_id})
    transfer = BikeTransfer(**transfer_in_db)
    if bike.state != BikeState.IN_TRANSFER and transfer.state != BikeTransferState.CLOSED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Bike is not in transfer")
    
    # Checks if the requester is also the receiver from a transfer
    if sender.id != transfer.sender:
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail=f"The receiver is not the same person in the transfer")
    
    # This hands over the ownership to the sender of the request
    bike.owner = sender.id
    bike.state = BikeState.TRANSFERABLE
    bike.claimed_date = datetime.datetime.now()
    transfer.state = BikeTransferState.CLOSED
    bike.save()
    transfer.save()

    return bike and transfer