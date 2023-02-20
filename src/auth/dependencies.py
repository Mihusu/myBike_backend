from dotenv import dotenv_values
from fastapi import HTTPException, Depends, status
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