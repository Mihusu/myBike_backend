from fastapi import APIRouter, Form

from src.notifications.sms import send_sms  

router = APIRouter(
    tags=['sms'], 
    prefix='/sms'
)

@router.get("/test", summary="Testing sending of an sms-message")
def test():
    send_sms(msg=f"Brug koden {'abcd123efghijk'} til at indløse din cykel. \n\n@mincykel.app #abcd123efghijk")
    
    
    




