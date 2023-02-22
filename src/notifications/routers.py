from fastapi import APIRouter

from src.notifications.sms import send_sms  

router = APIRouter(
    tags=['sms'], 
    prefix='/sms'
)

@router.get("/test", summary="Testing sending of an sms-message")
def test():
    send_sms(msg="Hello Cycler!")
    
    
    




