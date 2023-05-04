import datetime
import secrets
from typing import Any
import uuid
from pydantic import Field, PrivateAttr

from src.models import Entity

def generate_otp():
    """ Generates a string of digits of given length"""
    DIGIT_LENGTH = 6
    
    nums = range(0, 9)
    result = ""
    for _ in range(DIGIT_LENGTH):
        result += str(secrets.choice(nums))
    return result


class Session2FA(Entity):
    
    _COLLECTION_NAME = PrivateAttr(default='2fa_sessions')
    
    name: str
    otp:  str = Field(default_factory=generate_otp)     # It might be a good idea to hash this. Although there is an in-build security in the expiration time
    expires_at : datetime.datetime = Field(default_factory=lambda : datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=5))


class TrustDeviceSession(Session2FA):
    owner_id   : uuid.UUID
    ip_address : str
    

class BikeOwnerRegistrationSession(Session2FA):    
    hash: bytes
    phone_number: str
    request_ip_address: str
    created_at: datetime.datetime = Field(default_factory=lambda : datetime.datetime.now(datetime.timezone.utc))
    

class ResetPasswordSession(Session2FA):    
    phone_number: str           # Phone number of account trying to reset password
    verified : bool = False     # Only when this flag is set to true allows for a password change


class AccessSession(Entity):

    _COLLECTION_NAME = PrivateAttr(default='access_sessions')

    ip_address: str
    phone_number: str       # Phone number of owner trying to access
    login_attempts: int = 0
    otp: str = Field(default_factory=generate_otp)
    cooldown_expires_at: datetime.datetime = Field(default_factory=lambda : datetime.datetime.now(datetime.timezone.utc))
    #last_login_attempt_at: datetime