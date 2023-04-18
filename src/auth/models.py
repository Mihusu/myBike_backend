import datetime
import secrets
from typing import Any
import uuid
from pydantic import BaseModel, Field, PrivateAttr

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
    expires_at : datetime.datetime = Field(default_factory=lambda : datetime.datetime.now() + datetime.timedelta(minutes=5))


class TrustDeviceSession(Session2FA):
    owner_id   : uuid.UUID
    ip_address : str
    

class BikeOwnerSession(Entity):
    
    _COLLECTION_NAME = PrivateAttr(default='bikeowner_sessions')
    
    otp: str = Field(default_factory=generate_otp)      
    hash: bytes
    phone_number: str
    expires_in : datetime.datetime = Field(default_factory=lambda : datetime.datetime.now() + datetime.timedelta(minutes=5))


class ResetpasswordSession(Entity):
    
    _COLLECTION_NAME = PrivateAttr(default='resetpassword_sessions')
    
    phone_number: str           # Phone number of account trying to reset password
    otp: str = Field(default_factory=generate_otp)
    verified : bool = False     # Only when this flag is set to true allows for a password change
    expires_in : datetime.datetime = Field(default_factory=lambda : datetime.datetime.now() + datetime.timedelta(minutes=5))


class AccessSession(Entity):

    _COLLECTION_NAME = PrivateAttr(default='access_sessions')

    ip_address: str
    phone_number: str       # Phone number of owner trying to access
    login_attempts: int = 0
    otp: str = Field(default_factory=generate_otp)
    cooldown_expires_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    #last_login_attempt_at: datetime


class Device(BaseModel):
    ip_address : str
    name       : str | None = None


class DeviceList(BaseModel):
    white_list: list[Device] = []
    black_list: list[Device] = []
    
    def is_blacklisted(self, ip_addr: str):
        for device in self.black_list: 
            if device.ip_address == ip_addr:
                return True
        return False
    
    def is_known(self, ip_addr: str):
        for device in self.white_list:
            if device.ip_address == ip_addr:
                return True
        return False
    


