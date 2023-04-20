from fastapi import APIRouter, Depends, Request, status

from src.activities.responses import ActivityResponse
from src.auth.dependencies import authenticated_request
from src.bikes.models import Bike
from src.owners.models import BikeOwner
from src.transfers.models import BikeTransfer, BikeTransferState
from src.transfers.utils import expand_transfer


router = APIRouter(
    tags=['activities'],
    prefix='/activities'
)


@router.get('/', summary="Get all activities for a user", status_code=status.HTTP_200_OK)
def get_activities(request: Request, user: BikeOwner = Depends(authenticated_request)):
    
    outgoing_requests  = [expand_transfer(BikeTransfer(**transfer), request) for transfer in request.app.collections['transfers'].find({'sender' : user.id, 'state' : BikeTransferState.PENDING})]
    incoming_requests =  [expand_transfer(BikeTransfer(**transfer), request) for transfer in request.app.collections['transfers'].find({'receiver' : user.id, 'state' : BikeTransferState.PENDING})]
    completed_requests = [expand_transfer(BikeTransfer(**transfer), request) for transfer in request.app.collections['transfers'].find({
        '$and' : [
            {'$or' : [
                { 'sender' : user.id }, 
                { 'receiver' : user.id }
            ]},
            {'$or' : [
                { 'state' : BikeTransferState.ACCEPTED }, 
                { 'state' : BikeTransferState.DECLINED }
            ]}
        ]
    })]
    
    return {
        'alerts' : len(outgoing_requests) + len(incoming_requests),
        'outgoing_transfer_requests' : outgoing_requests,
        'incoming_transfer_requests' : incoming_requests,
        'completed_transfers' : completed_requests
    }
