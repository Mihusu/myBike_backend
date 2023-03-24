from fastapi import APIRouter, Depends, Request, status

from src.activities.responses import ActivityResponse
from src.auth.dependencies import authenticated_request
from src.bikes.models import BikeOwner
from src.transfers.models import BikeTransferState


router = APIRouter(
    tags=['activities'],
    prefix='/activities'
)


@router.get('/', summary="Get all activities for a user", status_code=status.HTTP_200_OK)
def get_activities(request: Request, user: BikeOwner = Depends(authenticated_request)) -> ActivityResponse:
    
    outgoing_requests = list(request.app.collections['transfers'].find({'sender' : user.id, 'state' : BikeTransferState.PENDING}))
    incomming_requests = list(request.app.collections['transfers'].find({'receiver' : user.id, 'state' : BikeTransferState.PENDING}))
    completed_requests = list(request.app.collections['transfers'].find({
        '$or' : [
            { 'sender' : user.id }, 
            { 'receiver' : user.id }
        ],
        '$or' : [
            { 'state' : BikeTransferState.ACCEPTED }, 
            { 'state' : BikeTransferState.DECLINED }
        ]
    }))
    
    return ActivityResponse(
        alerts=len(outgoing_requests) + len(incomming_requests),
        outgoing_transfer_requests=outgoing_requests,
        incomming_transfer_requests=incomming_requests,
        completed_transfers=completed_requests
    )