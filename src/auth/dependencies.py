import uuid
from dotenv import dotenv_values
from fastapi import Body, HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
from jose.exceptions import JOSEError

from src.bikes.models import BikeOwner

security = HTTPBearer(description="Paste in your access token here to be used in subsequent requests")

config = dotenv_values(".env")

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
    Authenticates the request by verifying the incomming jwt token and
    returns the user of the token
    """
    token_claims = jwt.decode(token, key=config['JWT_SECRET'])
    user = request.app.collections['bike_owners'].find_one({'_id': uuid.UUID(token_claims['sub']) })
    return BikeOwner(**user)
    
def phone_number_not_registered(request: Request, phone_number: str = Body()):
    """Check that given phonenumber does not already exist in the database"""
    bike_owner = request.app.collections['bike_owners'].find_one({'phone_number': phone_number})
    if bike_owner:
        raise HTTPException(status_code=400, detail=f"There already exist a bike owner with given phonenumber '{phone_number}'")
    
    return phone_number