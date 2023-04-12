from dotenv import dotenv_values
from fastapi import Body, Request

config = dotenv_values(".env")

def sanitize_phone_number(request: Request, phone_number: str = Body(embed=True)):
    """Sanitize phone number to conform with database format"""
    # Remove white spaces
    return phone_number.replace(" ", "")