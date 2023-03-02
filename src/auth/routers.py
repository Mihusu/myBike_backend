import datetime
import bcrypt
from dotenv import dotenv_values
from fastapi import APIRouter, Body, HTTPException, Depends, Request, status
from fastapi_jwt_auth import AuthJWT
from pydantic import BaseModel


from src.notifications.sms import send_sms
from src.auth.dependencies import has_access, phone_number_not_registered
from src.bikes.models import BikeOwnerCredentials
from src.auth.models import BikeOwnerSession


config = dotenv_values(".env")

router = APIRouter(
    tags=['authentication'], 
    prefix="/auth"
)

class Settings(BaseModel):
    authjwt_secret_key: str = config['JWT_SECRET']
    authjwt_access_token_expires: datetime.timedelta = datetime.timedelta(minutes=30)
    

@AuthJWT.load_config
def get_config():
    return Settings()


@router.post('/token', summary="Authenticate to get an access token")
def authenticate(request: Request, user: BikeOwnerCredentials, Authorize: AuthJWT = Depends()):
    
    # Verify correct user
    found_user = request.app.collections['bike_owners'].find_one({'phone_number': user.phone_number})
    if not found_user:
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail=f"Wrong phonenumber or password"
        )
    
    # Verify password
    
    return {
        "access_token": Authorize.create_access_token(subject=found_user['_id']),
        "refresh_token": Authorize.create_refresh_token(subject=found_user['_id'])
    }


@router.post('/register/me', summary="Register a new bike owner")
def register_bike_owner(request: Request, phone_number: str = Depends(phone_number_not_registered), password: str = Body()):
    
    #1. Check that phone number not already exists
    #1.5 Hash and salt password
    #2. Create and save new BikeOwnerSessiom object
    #3. Send sms with otp to phone_number
    
    hashed_password = bcrypt.hashpw(password.encode(encoding="utf-8"), bcrypt.gensalt())
    
    session = BikeOwnerSession(phone_number=phone_number, hash=str(hashed_password))
    #session.save()
    
    send_sms(
        msg=f"Din verifikations kode er: {session.otp}",
        to=phone_number
    )
    
    return {'session_id': session.id}




    


# To be removed once demonstrated
@router.get('/protected', summary="Example of a protected route")
def protected_route(token: str = Depends(has_access)):
    return {"access_granted", token}
