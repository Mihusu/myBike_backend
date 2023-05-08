from fastapi import APIRouter, Depends, Request, HTTPException, status
from jose import JOSEError

from src.owners.models import BikeOwner
from src.auth.dependencies import authenticated_request

router = APIRouter(
    tags=['owners'],
    prefix='/owners'
)

# TODO: could use an explanation of where this is used + some gardening, also why is the function called get_transfer?

@router.get('/me', summary="Get a single user's id and phone number", status_code=status.HTTP_200_OK)
def get_transfer(
    request: Request,
    user: BikeOwner = Depends(authenticated_request)) -> dict:

    response: dict = {"phone_number": user.phone_number,
                "user_id": user.id}
    print(response)
    
    try:
        return response
    
    except JOSEError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e))