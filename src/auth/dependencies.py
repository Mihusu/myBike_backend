import datetime
import uuid
from fastapi import Body, HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
from jose.exceptions import JOSEError
from src.dependencies import sanitize_phone_number

from src.settings import config
from src.owners.models import BikeOwner

security = HTTPBearer(description="Paste in your access token here to be used in subsequent requests")

class Verify2FASession:
    def __init__(self, name: str):
         self.name = name

    def __call__(self, request: Request, session_id: uuid.UUID = Body(), otp: str = Body()):
        session_doc = request.app.collections['2fa_sessions'].find_one({'_id': session_id})
        if not session_doc:
            raise HTTPException(
                status_code=400, detail=f"Non-existing session with session id: {session_id}")

        if not session_doc['name'] == self.name:
            raise HTTPException(
                status_code=403, detail=f"Verifying wrong kind of session. Verifying session with name '{self.name}' but got session '{session_doc['name']}'")
            
        if datetime.datetime.now(datetime.timezone.utc) > session_doc['expires_at']:
            raise HTTPException(
                status_code=410, detail=f"Session expired at: {session_doc['expires_at']}")

        if not otp == session_doc['otp']:
            raise HTTPException(status_code=403, detail=f"Invalid OTP")
        
        return session_doc

def valid_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    
    try:
        jwt.decode(token, key=config['JWT_SECRET'])
        return token
    except JOSEError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e))

def authenticated_request(request: Request, token = Depends(valid_token)) -> BikeOwner:
    """
    Authenticates the request by verifying the incoming jwt token and
    returns the user of the token
    """
    token_claims = jwt.decode(token, key=config['JWT_SECRET'])
    user = request.app.collections['bike_owners'].find_one({'_id': uuid.UUID(token_claims['sub']) })
    return BikeOwner(**user)
    
def phone_number_not_registered(request: Request, phone_number: str = Depends(sanitize_phone_number)):
    """Check that given phone number does not already exist in the database"""
    bike_owner = request.app.collections['bike_owners'].find_one({'phone_number': phone_number})
    if bike_owner:
        raise HTTPException(status_code=400, detail=f"There already exists a bike owner with given phone number '{phone_number}'")
    
    return phone_number

def strong_password(password: str = Body()):
    """ 
    Checks that the given password meets our requirements for a strong password
    
    Current requirements for strong password is:
        * A minimum of 12 characters
        * A maximum of 64 characters
        
    Last changed:    may.10.2023 - jsaad
    """
    MIN_PASSWORD_LEN = 12
    MAX_PASSWORD_LEN = 64
    
    if len(password) < MIN_PASSWORD_LEN:
        raise HTTPException(status_code=406, detail=f"Weak password. Password must contain atleast 12 characters")
    if len(password) > MAX_PASSWORD_LEN:
        raise HTTPException(status_code=406, detail=f"Lengthy password. Password must contain at most 64 characters")
    
    return password


        
    