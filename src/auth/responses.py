import datetime
import uuid
from pydantic import BaseModel


class AuthSuccessResponse(BaseModel):
    access_token:  str 
    refresh_token: str
    

class DeviceVerificationResponse(BaseModel):
    msg: str
    session_id : uuid.UUID

class InvalidCredentialsResponse(BaseModel):
    msg : str
    attempts_left : int
    

class AuthCooldownResponse(BaseModel):
    msg : str
    cooldown_expires_at : datetime.datetime


class DeviceBlacklisted(BaseModel):
    msg : str