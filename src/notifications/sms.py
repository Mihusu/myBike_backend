from dotenv import dotenv_values
import requests

config = dotenv_values(".env")

def send_sms(msg: str, to: str = "+4542240440"):
    
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