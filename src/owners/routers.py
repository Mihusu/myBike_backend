import uuid
import datetime
from fastapi import APIRouter, Body, Depends, Request, HTTPException, status
from jose import JOSEError

from src.owners.models import BikeOwner
from src.auth.dependencies import authenticated_request

router = APIRouter(
    tags=['owners'],
    prefix='/owners'
)


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