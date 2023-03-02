from dotenv import dotenv_values
from fastapi import Body, HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
from jose.exceptions import JOSEError

security = HTTPBearer(description="Paste in your access token here to be used in subsequent requests")

config = dotenv_values(".env")

def has_access(credentials: HTTPAuthorizationCredentials = Depends(security)):
    
    token = credentials.credentials
    
    try:
        jwt.decode(token, key=config['JWT_SECRET'])
        return token
    except JOSEError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e))
    
def phone_number_not_registered(request: Request, phone_number: str = Body()):
    """Check that given phonenumber does not already exist in the database"""
    bike_owner = request.app.collections['bike_owners'].find_one({'phone_number': phone_number})
    if bike_owner:
        raise HTTPException(status_code=400, detail=f"There already exist a bike owner with given phonenumber '{phone_number}'")
    
    return phone_number