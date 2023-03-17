import uuid
from fastapi import APIRouter, Depends, Form, Request, Response, HTTPException, UploadFile, File, status
from src.notifications.sms import send_sms
from src.storage.aws import save_file

router = APIRouter(
    tags=['transfers'],
    prefix='/transfers'
)

@router.post('/', response_description="creating a bike transfer")
def createTransfer(sender, receiver, bike_id, request: Request, response: Response):
    #check sender phone number exists
    #check bike exists
    #check sender owns bike
    #check bike not stolen
    #check bike not in transfer
    response.status_code = status.HTTP_201_CREATED
    return response