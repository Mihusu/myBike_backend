import datetime
import uuid
import bcrypt
import logging
from dotenv import dotenv_values
from fastapi import APIRouter, Body, HTTPException, Depends, Request, status
from fastapi_jwt_auth import AuthJWT
from pydantic import BaseModel

from src.owners.models import BikeOwner
from src.notifications.sms import send_sms
from src.auth.dependencies import strong_password, phone_number_not_registered, authenticated_request, valid_token
from src.dependencies import sanitize_phone_number
from src.auth.models import BikeOwnerSession, ResetpasswordSession, AccessSession, Device

logger = logging.getLogger(__name__)

config = dotenv_values(".env")

router = APIRouter(
    tags=['authentication'],
    prefix="/auth"
)

class Settings(BaseModel):
    authjwt_secret_key = config['JWT_SECRET']
    authjwt_access_token_expires: datetime.timedelta = datetime.timedelta(
        minutes=int(config['JWT_EXPIARY_TIME_MINS']))

@AuthJWT.load_config
def get_config():
    return Settings()

MAX_LOGIN_ATTEMPTS = 7
COOLDOWN_DURATIONS = {
    3: datetime.timedelta(seconds=10), 
    4: datetime.timedelta(seconds=30), 
    5: datetime.timedelta(minutes=5), 
    6: datetime.timedelta(minutes=15), 
    7: datetime.timedelta(minutes=30)
}

@router.post('/token', summary="Authenticate to get an access token")
async def authenticate(request: Request, phone_number: str = Body(), password: str = Body(), Authorize: AuthJWT = Depends()):

    # Verify bike owner exists
    owner_doc = request.app.collections['bike_owners'].find_one({'phone_number': phone_number})
    if not owner_doc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Bike owner not found")

    req_ip_address = request.client.host
    owner = BikeOwner(**owner_doc)

    # Start access session or use current access session
    current_ac_session = None
    ac_session_doc = request.app.collections['access_sessions'].find_one({
        'phone_number': phone_number,
        'ip_address'  : req_ip_address 
    })

    if not ac_session_doc:
        new_ac_session = AccessSession(ip_address=req_ip_address, phone_number=phone_number)
        new_ac_session.save()
        current_ac_session = new_ac_session
    else:
        current_ac_session = AccessSession(**ac_session_doc)

        # Check if user is in cooldown
        if current_ac_session.login_attempts >= 3 and current_ac_session.expires_at > datetime.datetime.now():
            time_left = current_ac_session.expires_at - datetime.datetime.now()
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail={
                "msg"           : "Too many failed login attempts. Please wait before trying again.",
                "time_left"     : time_left.total_seconds()
            })
    
    # Check that the device trying to authenticate is blacklisted
    for device in owner.devices.black_list: 
        if device.ip_address == req_ip_address:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Blacklisted ip-address: {req_ip_address}")
    
    # Verify password
    valid_password = bcrypt.checkpw(
        password=password.encode(encoding="utf-8"),
        hashed_password=owner_doc['hash']
    )

    if not valid_password:
            
        # Checks and calculate cooldown duration
        if current_ac_session.login_attempts >= 3:
            cooldown_duration = COOLDOWN_DURATIONS.get(current_ac_session.login_attempts, None)
            if cooldown_duration:
                current_ac_session.expires_at = datetime.datetime.now() + cooldown_duration
                current_ac_session.save()
            
            # Raise HTTPException with error message
            attempts_left = MAX_LOGIN_ATTEMPTS - current_ac_session.login_attempts
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={
                "msg"           : "Invalid credentials",
                "attempts_left" : attempts_left
            })

        if current_ac_session.login_attempts == MAX_LOGIN_ATTEMPTS:
            owner.devices.black_list.append(Device(ip_address=req_ip_address))

            logger.info(f"[{datetime.datetime.now()}] Failed login attempt from ip: {req_ip_address}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={
                "msg"           : "Invalid credentials",
                "attempts_left" : MAX_LOGIN_ATTEMPTS - current_ac_session.login_attempts
            })

        # Add one attempt to the current access session
        current_ac_session.login_attempts += 1
        current_ac_session.save()
            
    # Reset number of login attempts on success
    current_ac_session.login_attempts = 0
    current_ac_session.save()
    
    # Check if the device is already known
    known_device = False
    for device in owner.devices.white_list:
        if device.ip_address == req_ip_address:
            known_device = True
            break
    
    if not known_device:
        # Send back the access session id to client and send sms with verification OTP
        # to owner asking to verify this device
        send_sms(msg=
            f"""
            Hej! Nogle har forsøgt at logge ind fra en ukendt enhed med ip: '{req_ip_address}'.
        For at bekræfte enheden skal du bruge koden: {current_ac_session.otp}
        Hvis det ikke er dig bør du skifte din adgangskode. Det kan ikke lade sig gøre at logge ind uden verifikationskoden
            """,
            to=phone_number
        )
        return {
            "detail" : "Password attempt from unknown device. Please verify device.",
            "access_session_id" : current_ac_session.id
        }
    
    # Device is whitelisted and password is correct
    return {
        "access_token": Authorize.create_access_token(subject=str(owner_doc['_id'])),
        "refresh_token": Authorize.create_refresh_token(subject=str(owner_doc['_id']))
    }


@router.post('/')
@router.post('/register/me', summary="Register a new bike owner")
def register_bike_owner(request: Request, phone_number: str = Depends(phone_number_not_registered), password: str = Body()):

    MIN_PASSWORD_LEN = 12

    # 1. Check that phone number does not already exists
    # 1.25 Validate password against OWASP standards
    # 1.5 Hash and salt password
    # 2. Create and save new BikeOwnerSessiom object
    # 3. Send sms with otp to phone_number
    if len(password) < MIN_PASSWORD_LEN:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Weak password. Password must be equal or larger than 12 characters")

    hashed_password = bcrypt.hashpw(
        password.encode(encoding="utf-8"), bcrypt.gensalt())

    session = BikeOwnerSession(phone_number=phone_number, hash=hashed_password)
    session.save()

    send_sms(
        msg=f"Din verifikations kode er: {session.otp}",
        to=phone_number
    )

    return {'session_id': session.id}


@router.post('/register/me/check-otp', summary="Verify OTP of bike owner registration", status_code=status.HTTP_201_CREATED)
def verify_otp(request: Request, otp: str = Body(), session_id: uuid.UUID = Body()):

    # 1. Look up the session with given id
    # 2. Check that the session is not expired
    # 3. Check that the otp matches
    # 4. Create BikeOwner with given session details
    # 5. Generate token pair

    session = request.app.collections['bikeowner_sessions'].find_one({
                                                                     '_id': session_id})
    if not session:
        raise HTTPException(
            status_code=400, detail=f"Non-existing session with session id: {session_id}")

    if datetime.datetime.now() > session['expires_in']:
        raise HTTPException(
            status_code=403, detail=f"Session expired at: {session['expires_in']}")

    if not otp == session['otp']:
        raise HTTPException(status_code=403, detail=f"Invalid OTP")

    # Transfer over info from session object to bike owner details
    bike_owner = BikeOwner(
        phone_number=session['phone_number'], hash=session['hash'])
    bike_owner.save()

    # Maybe remove the session as the registration was successful?
    Authorize = AuthJWT()
    return {
        "access_token": Authorize.create_access_token(subject=str(bike_owner.id)),
        "refresh_token": Authorize.create_refresh_token(subject=str(bike_owner.id))
    }

@router.put('/reset-password/request', summary="Request a password reset in case of lost or compromised account")
def request_password_reset(request: Request, phone_number: str = Depends(sanitize_phone_number)):
    
    # Find the user with given phonenumber
    owner = request.app.collections['bike_owners'].find_one({'phone_number' : phone_number})
    if not owner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Bike owner with phonenumber '{phone_number}' not found")
    
    # Start a new password reset session with the owner
    session = ResetpasswordSession(phone_number=phone_number)
    session.save()
    # Send an sms with a OTP to the phonenumber saying
    # that they are trying to reset their password
    send_sms(to = phone_number, msg=f"Hej\nDin nulstillingskode er: {session.otp}\nDet kan ikke lade sig gøre at nulstille adgangskoden uden denne kode.")
    
    return {
        'session_id' : session.id,
        'expires_in' : session.expires_in
    }
    
@router.put('/reset-password/verify', summary="Verify the OTP comming from a password reset request", status_code=200)
def verify_password_reset(request: Request, session_id: uuid.UUID = Body(), otp: str = Body()):
    
    session_doc = request.app.collections['resetpassword_sessions'].find_one({'_id' : session_id})
    if not session_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session '{session_id}' not found")
    
    session = ResetpasswordSession(**session_doc)
    
    if session.expires_in < datetime.datetime.now():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Session '{session_id}' expired at {session.expires_in}")
    
    if not session.otp == otp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid OTP for session '{session_id}'")
    
    # All checks okay. Set the session to be verified
    session.verified = True
    session.save()
    
@router.put('/reset-password/confirm', summary="Changes an accounts password", status_code=200)
def confirm_password_reset(request: Request, session_id: uuid.UUID = Body(), password: str = Depends(strong_password)):
    
    session_doc = request.app.collections['resetpassword_sessions'].find_one({'_id' : session_id})
    if not session_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session '{session_id}' not found")
    
    session = ResetpasswordSession(**session_doc)
    if not session.verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Session '{session_id}' is missing verification")
    
    # Session is verified, change the password of the account.
    owner_doc = request.app.collections['bike_owners'].find_one({'phone_number' : session.phone_number})
    
    owner      = BikeOwner(**owner_doc)
    owner.hash = bcrypt.hashpw(password.encode(encoding="utf-8"), bcrypt.gensalt())
    owner.save()
    
    send_sms(msg="Din adgangskode er blevet nulstillet", to=session.phone_number)
    
    # Remove the reset password session to prevent future access to this verified session.
    request.app.collections['resetpassword_sessions'].delete_one({'_id' : session_id})
    
    
    
# TODO: Make a dependency for trimming phone number
# TODO: Make a dependency for securing that passwords meets password requirements
# To be removed once demonstrated


@router.get('/protected', summary="Example of a protected route")
def protected_route(token: str = Depends(valid_token)):
    return {"access_granted", token}


@router.get('/protected-with.user', summary="Example of a protected route that gets the user profile")
def protected_route_user(user: BikeOwner = Depends(authenticated_request)):
    return user
