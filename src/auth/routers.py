import datetime
import uuid
import bcrypt
from dotenv import dotenv_values
from fastapi import APIRouter, Body, HTTPException, Depends, Request, status
from fastapi_jwt_auth import AuthJWT
from pydantic import BaseModel

from src.owners.models import BikeOwner
from src.notifications.sms import send_sms
from src.auth.dependencies import authenticated_request, valid_token, phone_number_not_registered
from src.auth.models import BikeOwnerSession


config = dotenv_values(".env")

router = APIRouter(
    tags=['authentication'], 
    prefix="/auth"
)

class Settings(BaseModel):
    authjwt_secret_key = config['JWT_SECRET']
    authjwt_access_token_expires: datetime.timedelta = datetime.timedelta(minutes=int(config['JWT_EXPIARY_TIME_MINS']))
    

@AuthJWT.load_config
def get_config():
    return Settings()


@router.post('/token', summary="Authenticate to get an access token")
def authenticate(request: Request, phone_number: str = Body(), password: str = Body(), Authorize: AuthJWT = Depends()):
    
    # Verify user exists
    found_user = request.app.collections['bike_owners'].find_one({'phone_number': phone_number})
    if not found_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Bike owner not found")
    
    # Verify password
    valid_password = bcrypt.checkpw(
        password=password.encode(encoding="utf-8"),  #TODO: Check for right conversion between str & bytes
        hashed_password=found_user['hash']
    )
    if not valid_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid credentials")
    
    return {
        "access_token": Authorize.create_access_token(subject=str(found_user['_id'])),
        "refresh_token": Authorize.create_refresh_token(subject=str(found_user['_id']))
    }

@router.post('/register/me', summary="Register a new bike owner")
def register_bike_owner(request: Request, phone_number: str = Depends(phone_number_not_registered), password: str = Body()):
    
    MIN_PASSWORD_LEN = 12
    
    #1. Check that phone number does not already exists
    #1.25 Validate password against OWASP standards
    #1.5 Hash and salt password
    #2. Create and save new BikeOwnerSessiom object
    #3. Send sms with otp to phone_number
    if len(password) < MIN_PASSWORD_LEN:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Weak password. Password must be equal or larger than 12 characters")
    
    hashed_password = bcrypt.hashpw(password.encode(encoding="utf-8"), bcrypt.gensalt())
    
    session = BikeOwnerSession(phone_number=phone_number, hash=hashed_password)
    session.save()
    
    send_sms(
        msg=f"Din verifikations kode er: {session.otp}",
        to=phone_number
    )
    
    return {'session_id': session.id}

@router.post('/register/me/check-otp', summary="Verify OTP of bike owner registration", status_code=status.HTTP_201_CREATED)
def verify_otp(request: Request, otp: str = Body(), session_id: uuid.UUID = Body()):
    
    #1. Look up the session with given id
    #2. Check that the session is not expired
    #3. Check that the otp matches
    #4. Create BikeOwner with given session details
    #5. Generate token pair
    
    session = request.app.collections['bikeowner_sessions'].find_one({'_id': session_id})
    if not session:
        raise HTTPException(status_code=400, detail=f"Non-existing session with session id: {session_id}")
    
    if datetime.datetime.now() > session['expires_in']:
        raise HTTPException(status_code=403, detail=f"Session expired at: {session['expires_in']}")
    
    if not otp == session['otp']:
        raise HTTPException(status_code=403, detail=f"Invalid OTP")
    
    # Transfer over info from session object to bike owner details
    bike_owner = BikeOwner(phone_number=session['phone_number'], hash=session['hash'])
    bike_owner.save()
    
    # Maybe remove the session as the registration was successful?
    Authorize = AuthJWT()
    return {
        "access_token": Authorize.create_access_token(subject=str(bike_owner.id)),
        "refresh_token": Authorize.create_refresh_token(subject=str(bike_owner.id))
    }

# To be removed once demonstrated
@router.get('/protected', summary="Example of a protected route")
def protected_route(token: str = Depends(valid_token)):
    return {"access_granted", token}

@router.get('/protected-with.user', summary="Example of a protected route that gets the user profile")
def protected_route_user(user: BikeOwner = Depends(authenticated_request)):
    return user