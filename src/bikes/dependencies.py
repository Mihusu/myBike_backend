import re as regex
from fastapi import Form, HTTPException, Request

def frame_number_not_registered(request: Request, frame_number: str = Form(...)):
    """Checks that the frame number is not already in the database"""
    bike = request.app.collections['bikes'].find_one({'frame_number': frame_number.lower()})
    if bike:
        raise HTTPException(status_code=400, detail=f"Bike with frame number '{frame_number}' is already registered")

def valid_frame_number(frame_number: str = Form(...)):
    """ Validates the frame number according to the danish frame number format

    MANUFACTURER_NUMBER | SERIAL_NUMBER | YEAR_MARK

    MANUFACTUER_NUMBER  : 1..4 characters
    SERIAL_NUMBER       : 1..* digits
    YEAR_MARK           : 1 character

    @See: https://da.wikipedia.org/wiki/Det_danske_stelnummersystem_for_cykler for more info
    """
    valid = regex.search("^[a-zA-Z]{1,4}[0-9]+[a-zA-Z]$", frame_number)
    if valid:
        return frame_number
    else:
        raise ValueError(f"Invalid frame number. See https://da.wikipedia.org/wiki/Det_danske_stelnummersystem_for_cykler for valid frame numbers")

def valid_danish_phone_number(phone_number: str = Form(...)):
    trimmed = phone_number.replace(' ', '')
    valid = regex.search('^(\+45)?[0-9]{8}', trimmed)
    if not valid:
        raise ValueError("Invalid phonenumber. Currently only danish phonenumbers are valid")
        