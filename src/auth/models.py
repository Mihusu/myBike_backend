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


class AccessSession(Entity):

    _COLLECTION_NAME = PrivateAttr(default='access_sessions')

    ip_address: str
    phone_number: str       # Phone number of owner trying to access
    login_attempts: int = 0
    otp: str = Field(default_factory=generate_otp)
    cooldown_expires_at: datetime.datetime = Field(default_factory= lambda : datetime.datetime.now(datetime.timezone.utc))
    sms_cooldown_expires_at: datetime.datetime = Field(default_factory= lambda : datetime.datetime.now(datetime.timezone.utc))
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
    


