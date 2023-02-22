from fastapi import Form, APIRouter, Body, Request, Response, HTTPException, status
from twilio.twiml.messaging_response import MessagingResponse
from twilio.request_validator import RequestValidator

from src.notifications.sms import send_sms  

router = APIRouter(
    tags=['sms'], 
    prefix='/sms'
)

@router.get("/test")
def test():
    send_sms(msg="Hello Cycler!")
    
    
    




