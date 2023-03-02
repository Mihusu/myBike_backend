
import datetime
import secrets
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


class BikeOwnerSession(Entity):
    
    _COLLECTION_NAME = PrivateAttr(default='bikeowner_sessions')
    
    otp: str = Field(default_factory=generate_otp)      # It might be a good idea to hash this. Although there is an in-build security in the expiration time
    hash: str
    phone_number: str
    expires_in : datetime.datetime = Field(default=datetime.datetime.now() + datetime.timedelta(minutes=5))