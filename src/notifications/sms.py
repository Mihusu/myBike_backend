import requests
from src.settings import config

def send_sms(msg: str, to: str):
    
    if config['SMS_ENABLED'] == 'NO':
        return False
    
    API_URL = f"https://api.twilio.com/2010-04-01/Accounts/{config['TWILLIO_ACCOUNT_SID']}/Messages.json"

    response = requests.post(
        API_URL, 
        data={
            "Body" : msg,
            "From" : config['TWILLIO_SENDER_PHONE_NUMBER'],
            "To"   : to
        },
        auth=(config['TWILLIO_ACCOUNT_SID'], config['TWILLIO_AUTH_TOKEN'])
    )

    # Error and success handling
    return response.ok