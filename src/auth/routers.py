import datetime
from dotenv import dotenv_values
from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi_jwt_auth import AuthJWT

from pydantic import BaseModel

from src.auth.dependencies import has_access
from src.bikes.models import BikeOwnerCredentials


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

# To be removed once demonstrated
@router.get('/protected', summary="Example of a protected route")
def protected_route(token: str = Depends(has_access)):
    return {"access_granted", token}
