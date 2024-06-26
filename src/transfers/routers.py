import uuid
import datetime
from fastapi import APIRouter, Body, Depends, Request, HTTPException, status

from src.bikes.models import Bike, BikeState
from src.owners.models import BikeOwner
from src.auth.dependencies import authenticated_request
from src.transfers.models import BikeTransfer, BikeTransferState
from src.transfers.dependencies import bike_with_id_exists
from src.transfers.utils import expand_transfer


router = APIRouter(
    tags=['transfers'],
    prefix='/transfers'
)


@router.get('/{transfer_id}', summary="Get a single transfer", status_code=status.HTTP_200_OK)
def get_transfer(request: Request, transfer_id: uuid.UUID, user: BikeOwner = Depends(authenticated_request)):
    
    transfer_in_db = request.app.collections['transfers'].find_one({'_id' : transfer_id})
    
    if not transfer_in_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No such transfer found")
    
    transfer = BikeTransfer(**transfer_in_db)
    
    # Check that the user is allowed to see the transfer
    permission_to_view = transfer.sender == user.id or transfer.receiver == user.id
    if not permission_to_view:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"View of transfer not allowed")
    
    return expand_transfer(transfer, request)


@router.post('', description="creating a bike transfer", status_code=status.HTTP_201_CREATED)
def create_transfer(
    request: Request, 
    sender: BikeOwner = Depends(authenticated_request), 
    receiver_phone_number = Body(), 
    bike_id: uuid.UUID = Depends(bike_with_id_exists)
) -> BikeTransfer:
    
    # Check receiver exists
    receiver_in_db = request.app.collections["bike_owners"].find_one({"phone_number": receiver_phone_number})
    if not receiver_in_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Bike owner with phone number {receiver_phone_number} not found")
        
    # Check bike exists
    # is done in dependencies

    # Check sender owns bike
    bike_owner_in_db = request.app.collections["bikes"].find_one({"owner": sender.id})
    if not bike_owner_in_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Bike owner with phone number {sender.phone_number} does not own bike with id {bike_id}")
    
    # Check sender is not also receiver
    receiver = BikeOwner(**receiver_in_db)
    if sender.id == receiver.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"System does not allow transferral of a bike to yourself")

    # Check bike not stolen
    bike_in_db = request.app.collections["bikes"].find_one({"_id": bike_id})
    bike = Bike(**bike_in_db)
    if bike.reported_stolen:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Bike is reported stolen. Transfer disallowed")
    
    # Check bike is transferable
    if not bike.state == BikeState.TRANSFERABLE:
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail=f"Bike is already in transfer or not transferable")
    
    # Make a transfer object
    transfer_info = {
        'sender': sender.id, 
        'receiver': receiver_in_db["_id"],
        'bike_id': bike_id,
    }

    transfer = BikeTransfer(**transfer_info)
    bike.state = BikeState.IN_TRANSFER

    bike.save()

    # Return transfer object to request sender
    return transfer.save()

@router.put('/{transfer_id}/retract',
            description="retracting a bike transfer",
            status_code=status.HTTP_202_ACCEPTED)
def retract_transfer(
    transfer_id: uuid.UUID,
    request: Request,
    requester: BikeOwner = Depends(authenticated_request)
    ):
    
    transfer_in_db: BikeTransfer = request.app.collections["transfers"].find_one({"_id": transfer_id})
    transfer = BikeTransfer(**transfer_in_db)

    # Check transfer exist
    if not transfer_in_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No such transfer found")
    
    # Check transfer pending
    if not transfer.state == BikeTransferState.PENDING:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Transfer is not pending. Cannot decline transfer")

    # Check sender is original transferer 
    if not requester.id == transfer.sender:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Requester id does not match original transferer. Cannot decline transfer")
    
    # Update bike state
    bike_in_db: Bike = request.app.collections["bikes"].find_one({"_id": transfer.bike_id})
    bike = Bike(**bike_in_db)
    bike.state = BikeState.TRANSFERABLE
    bike.save()

    delete_result = request.app.collections["transfers"].delete_one({"_id": transfer_id})
    print(delete_result)
    if not delete_result.deleted_count == 1:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"failed to delete transfer with id {transfer_id}")
    
    return {"message": "transfer deleted successfully"}
    

@router.put('/{transfer_id}/accept', description="Accepts a bike transfer", status_code=status.HTTP_202_ACCEPTED)
def accept_transfer(
    transfer_id: uuid.UUID,
    request: Request, 
    requester: BikeOwner = Depends(authenticated_request)
) -> BikeTransfer:

    # Check transfer exists
    transfer_in_db = request.app.collections["transfers"].find_one({"_id": transfer_id})
    if not transfer_in_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Transfer is not in system")
    
    transfer = BikeTransfer(**transfer_in_db)
    
    # Check bike exists
    bike_in_db = request.app.collections["bikes"].find_one({"_id": transfer.bike_id})
    if not bike_in_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Bike is not in system")
    
    # Checks the bike is not stolen
    bike = Bike(**bike_in_db)
    if bike.reported_stolen:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Bike is reported stolen. Transfer disallowed")

    # Checks bike is in transfer and transfer is pending
    if bike.state != BikeState.IN_TRANSFER or transfer.state != BikeTransferState.PENDING:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Bike is not in a transferable state or transfer state not valid")
    
    # Checks if the requester is also the receiver from a transfer
    if requester.id != transfer.receiver:
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail=f"Requester is not recipient in the transfer")
    
    # This hands over the ownership to the sender of the request
    bike.owner = requester.id
    bike.state = BikeState.TRANSFERABLE
    transfer.state = BikeTransferState.ACCEPTED
    transfer.closed_at = datetime.datetime.now(datetime.timezone.utc)

    bike.save()

    return transfer.save()

@router.put('/{transfer_id}/reject', description="Rejects a bike transfer", status_code=status.HTTP_202_ACCEPTED)
def reject_transfer(
    transfer_id: uuid.UUID,
    request: Request, 
    requester: BikeOwner = Depends(authenticated_request), 
) -> BikeTransfer:
         
    # Get transfer
    transfer_in_db = request.app.collections["transfers"].find_one({"_id": transfer_id})
    transfer = BikeTransfer(**transfer_in_db)

    # Checks if the requester is also the receiver in a transfer
    if not requester.id == transfer.receiver:
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail=f"Requester does not match transfer recipient")
    
    # Get bike
    bike_in_db = request.app.collections["bikes"].find_one({"_id": transfer.bike_id})
    bike = Bike(**bike_in_db)
    
    # Checks bike is in transfer and transfer is pending
    if not bike.state == BikeState.IN_TRANSFER or not transfer.state == BikeTransferState.PENDING:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Bike not in transfer or transfer not pending")
    
    # This does not hand over the ownership to the sender of the request
    bike.state = BikeState.TRANSFERABLE
    transfer.state = BikeTransferState.DECLINED
    transfer.closed_at = datetime.datetime.now(datetime.timezone.utc)

    bike.save()

    return transfer.save()