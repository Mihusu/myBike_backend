import datetime
import uuid
import bcrypt
import logging
from fastapi import APIRouter, Body, HTTPException, Depends, Request, status
from fastapi_jwt_auth import AuthJWT
from pydantic import BaseModel

from src.settings import config
from src.owners.models import BikeOwner
from src.notifications.sms import send_sms
from src.auth.dependencies import Verify2FASession, strong_password, phone_number_not_registered
from src.dependencies import sanitize_phone_number
from src.auth.models import AccessSession, Device
from src.auth.responses import AuthSuccessResponse, DeviceBlacklisted, DeviceVerificationResponse, InvalidCredentialsResponse, DeviceVerifyCooldownResponse, AuthCooldownResponse
from src.auth.sessions import BikeOwnerRegistrationSession, ResetPasswordSession, TrustDeviceSession

logger = logging.getLogger(__name__)

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


@router.post('/token', summary="Authenticate to get an access token", responses={
    '200': {'model': AuthSuccessResponse, 'description': "Successfull authentication"},
    '307': {'model': DeviceVerificationResponse, 'description': "Credentials were valid, but the device is unknown and needs to be verified"},
    '401': {'model': InvalidCredentialsResponse, 'description': "Invalid phonenumber or password"},
    '404': {'description': "Account not registered"},
    '423': {'model': DeviceBlacklisted, 'description': "Device blacklisted because of too many failed attempts"},
    '425': {'model': DeviceVerifyCooldownResponse, 'description': "Device risks processing a request that might be replayed"},
    '429': {'model': AuthCooldownResponse, 'description': "Cooldown because of too many failed attempts"}
})

async def authenticate(request: Request, phone_number: str = Body(), password: str = Body(), Authorize: AuthJWT = Depends()):

    req_ip_address = request.client.host

    MAX_ATTEMPTS_BEFORE_COOLDOWN = 3
    MAX_ATTEMPTS_BEFORE_BLACKLIST = 7

    COOLDOWN_DURATIONS = {
        # Should start at MAX_ATTEMPTS_BEFORE_COOLDOWN
        3: datetime.timedelta(seconds=15),
        4: datetime.timedelta(seconds=30),
        5: datetime.timedelta(minutes=1),
        6: datetime.timedelta(minutes=1),
        # Should end one before MAX_ATTEMPTS_BEFORE_BLACKLIST
        7: datetime.timedelta(minutes=1),
    }

    # Verify bike owner exists
    owner_doc = request.app.collections['bike_owners'].find_one(
        {'phone_number': phone_number})
    if not owner_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Bike owner not found")

    owner = BikeOwner(**owner_doc)

    # Check that the requester is not blacklisted
    if owner.devices.is_blacklisted(req_ip_address):
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail={
                            "Blacklisted ip-address: {req_ip_address}"})

    # Start access session or use current access session
    current_ac_session = None
    ac_session_doc = request.app.collections['access_sessions'].find_one({
        'phone_number': phone_number,
        'ip_address': req_ip_address
    })

    if not ac_session_doc:
        new_ac_session = AccessSession(
            ip_address=req_ip_address, phone_number=phone_number)
        new_ac_session.save()
        current_ac_session = new_ac_session
    else:
        current_ac_session = AccessSession(**ac_session_doc)

    # Check if session cooldown is expired
    on_cooldown = current_ac_session.cooldown_expires_at > datetime.datetime.now(datetime.timezone.utc)
    if on_cooldown:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail={
            "msg": "Too many failed login attempts. Please wait before trying again.",
            "cooldown_expires_at": str(current_ac_session.cooldown_expires_at)
        })

    # Verify password
    valid_password = bcrypt.checkpw(
        password=password.encode(encoding="utf-8"),
        hashed_password=owner_doc['hash']
    )

    if not valid_password:

        # Add one attempt to the current access session
        current_ac_session.login_attempts += 1

        # Checks and adds cooldown penalty if necessary
        if current_ac_session.login_attempts >= MAX_ATTEMPTS_BEFORE_COOLDOWN and current_ac_session.login_attempts < MAX_ATTEMPTS_BEFORE_BLACKLIST:
            current_ac_session.cooldown_expires_at = datetime.datetime.now(datetime.timezone.utc) + COOLDOWN_DURATIONS[current_ac_session.login_attempts]
            current_ac_session.save()

            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail={
                "msg": "Too many failed login attempts. Please wait before trying again.",
                "cooldown_expires_at": str(current_ac_session.cooldown_expires_at)
            })

        # Check if device should be blacklisted
        if current_ac_session.login_attempts == MAX_ATTEMPTS_BEFORE_BLACKLIST:

            if owner.devices.is_known(req_ip_address):
                # User have gone above max attempts but is on the whitelist.
                # We don't want to permanently block them out of their account so
                # we just give them an extra try and add cd.
                current_ac_session.cooldown_expires_at = datetime.datetime.utcnow(
                ) + COOLDOWN_DURATIONS[current_ac_session.login_attempts]
                current_ac_session.login_attempts -= 1
                current_ac_session.save()

                logger.info(
                    f"[{datetime.datetime.now(datetime.timezone.utc)}] Failed login attempt from ip: {req_ip_address}")
                raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail={
                    "msg": "Too many failed login attempts. Please wait before trying again.",
                    "cooldown_expires_at": str(current_ac_session.cooldown_expires_at)
                })
            else:
                owner.devices.black_list.append(
                    Device(ip_address=req_ip_address))

                logger.info(
                    f"[{datetime.datetime.now(datetime.timezone.utc)}] Failed login attempt from ip: {req_ip_address}")
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={
                    "msg": "Invalid credentials. Too many attempts, your device has been blacklisted",
                    "attempts_left": 0
                })

        # Save modifications
        current_ac_session.save()

        logger.info(
            f"[{datetime.datetime.now(datetime.timezone.utc)}] Failed login attempt from ip: {req_ip_address}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={
            "msg": "Invalid credentials",
            "attempts_left": MAX_ATTEMPTS_BEFORE_BLACKLIST - current_ac_session.login_attempts
        })

    # Successful login attempt, reset number of login attempts
    current_ac_session.login_attempts = 0
    current_ac_session.save()

    # Check if the device is already known
    if not owner.devices.is_known(req_ip_address):

        SMS_COOLDOWN = datetime.timedelta(minutes=2)

        # Check if user is still on cooldown
        sms_on_cooldown = current_ac_session.sms_cooldown_expires_at > datetime.datetime.now(datetime.timezone.utc)
        if sms_on_cooldown:
            raise HTTPException(status_code=status.HTTP_425_TOO_EARLY, detail={
                "msg": "There's recently been attempted an login from your device",
                "cooldown_expires_at": str(current_ac_session.sms_cooldown_expires_at)
            })
        
        session = TrustDeviceSession(
            name='trust-device', owner_id=owner.id, ip_address=req_ip_address)
        session.save()

        send_sms(
            msg=f"Hej!\n\nNogle har forsøgt at logge ind fra en ukendt enhed med ip: '{req_ip_address}'.\n\nFor at bekræfte enheden skal du bruge koden: {session.otp}\n\nHvis det ikke er dig bør du skifte din adgangskode. Det kan ikke lade sig gøre at logge ind uden verifikationskoden",
            to=phone_number
        )

        # Sets a cooldown timer for sending an SMS to the user
        current_ac_session.sms_cooldown_expires_at = datetime.datetime.now(datetime.timezone.utc) + SMS_COOLDOWN
        current_ac_session.save()

        raise HTTPException(status_code=status.HTTP_307_TEMPORARY_REDIRECT, detail={
            "msg": "Password attempt from unknown device. Please verify device",
            "session_id": str(session.id)
        })

    # Device is whitelisted and password is correct
    return {
        "access_token": Authorize.create_access_token(subject=str(owner_doc['_id'])),
        "refresh_token": Authorize.create_refresh_token(subject=str(owner_doc['_id']))
    }


@router.put('/trust-device', status_code=200)
def trust_device(request: Request, session=Depends(Verify2FASession('trust-device')), device_name: str = Body()):
    session = TrustDeviceSession(**session)

    # Add the device to the owners whitelist
    owner_doc = request.app.collections['bike_owners'].find_one(
        {'_id': session.owner_id})
    owner = BikeOwner(**owner_doc)

    owner.devices.white_list.append(
        Device(name=device_name, ip_address=session.ip_address))
    owner.save()


@router.post('/register/me', summary="Register a new bike owner")
def register_bike_owner(request: Request, phone_number: str = Depends(phone_number_not_registered), password: str = Depends(strong_password)):

    # 1. Check that phone number does not already exists
    # 1.25 Validate password against OWASP standards
    # 1.5 Hash and salt password
    hashed_password = bcrypt.hashpw(
        password.encode(encoding="utf-8"), bcrypt.gensalt())

    # 1.75 Check whether a session for phone number and ip already exists
    request_ip = request.client.host
    print(request.client)
    print(request_ip)
    # Find the last entry
    existing_session = request.app.collections["2fa_sessions"].find_one({'request_ip_address': request_ip, 'name': 'bikeowner-registration'}, sort=[('$natural',-1)])
    print(existing_session)
    # print(now)

    # If a session is found, check time since creation to prevent SMS spam to phone number
    # If 60 seconds have passed allow creation of new registration session
    if existing_session:
        current_session = BikeOwnerRegistrationSession(**existing_session)
        time_delta = datetime.datetime.now(datetime.timezone.utc) - current_session.created_at
        if (time_delta.seconds < 300):
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail={
                "msg": f"You already have an active registration session. Please wait {300 - time_delta.seconds} seconds before trying again",
                "cooldown_expires_at": str(current_session.expires_at)
                })
        else:
            print(f"td seconds is {time_delta.seconds}, cooldown is over. Permission granted")

    # 2. Create and save new BikeOwnerSession object
    session = BikeOwnerRegistrationSession(
        name='bikeowner-registration', phone_number=phone_number, hash=hashed_password, request_ip_address=request_ip)
    session.save()

    # 3. Send sms with otp to phone_number
    send_sms(
        msg=f"Din verifikations kode er: {session.otp}",
        to=phone_number
    )

    return {
        'session_id': session.id,
        'expires_at': session.expires_at
    }


@router.post('/register/me/check-otp', summary="Verify OTP of bike owner registration", status_code=status.HTTP_201_CREATED)
def verify_bikeowner_registration(request: Request, session=Depends(Verify2FASession('bikeowner-registration'))):
    session = BikeOwnerRegistrationSession(**session)

    # Transfer over info from session object to bike owner details
    bike_owner = BikeOwner(
        phone_number=session.phone_number, hash=session.hash)
    
    # Add owner's current ip to whitelist
    req_ip_address = request.client.host
    device = Device(ip_address=req_ip_address, name="default")
    bike_owner.devices.white_list.append(device)

    bike_owner.save()

    # Maybe remove the session as the registration was successful? Implemented
    request.app.collections['2fa_sessions'].delete_one({'_id': session.id})
    

    Authorize = AuthJWT()
    return {
        "access_token": Authorize.create_access_token(subject=str(bike_owner.id)),
        "refresh_token": Authorize.create_refresh_token(subject=str(bike_owner.id))
    }


@router.put('/reset-password/request', summary="Request a password reset in case of lost or compromised account")
def request_password_reset(request: Request, phone_number: str = Depends(sanitize_phone_number)):

    # Find the user with given phonenumber
    owner = request.app.collections['bike_owners'].find_one(
        {'phone_number': phone_number})
    if not owner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Bike owner with phonenumber '{phone_number}' not found")
    
    existing_session = request.app.collections["2fa_sessions"].find_one({'phone_number': phone_number, 'name': 'password-reset'}, sort=[('$natural',-1)])

    if existing_session:
        current_session = ResetPasswordSession(**existing_session)
        sms_on_cooldown = current_session.expires_at > datetime.datetime.now(datetime.timezone.utc)
        if sms_on_cooldown:
            raise HTTPException(status_code=status.HTTP_425_TOO_EARLY, detail={
                "msg": "There's recently been requested a reset password attempt",
                "cooldown_expires_at": str(current_session.expires_at)
            })

    # Start a new password reset session with the owner
    current_rp_session = ResetPasswordSession(
        name='password-reset', phone_number=phone_number)
    current_rp_session.save()

    # Send an sms with a OTP to the phonenumber saying
    # that they are trying to reset their password
    send_sms(to=phone_number,
             msg=f"Hej\nDin nulstillingskode er: {current_rp_session.otp}\nDet kan ikke lade sig gøre at nulstille adgangskoden uden denne kode.")

    return {
        'session_id': current_rp_session.id,
        'expires_at': current_rp_session.expires_at
    }


@router.put('/reset-password/verify', summary="Verify the OTP coming from a password reset request", status_code=200)
def verify_password_reset(request: Request, session=Depends(Verify2FASession('password-reset'))):
    session = ResetPasswordSession(**session)

    # All checks okay. Set the session to be verified so that the user can
    # now make a new password
    session.verified = True
    session.save()


@router.put('/reset-password/confirm', summary="Changes an accounts password", status_code=200)
def confirm_password_reset(request: Request, session_id: uuid.UUID = Body(), password: str = Depends(strong_password)):

    session_doc = request.app.collections['2fa_sessions'].find_one({
                                                                   '_id': session_id})
    if not session_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Session '{session_id}' not found")

    session = ResetPasswordSession(**session_doc)
    if not session.verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Session '{session_id}' is missing verification")

    # Session is verified, change the password of the account.
    owner_doc = request.app.collections['bike_owners'].find_one(
        {'phone_number': session.phone_number})

    owner = BikeOwner(**owner_doc)
    owner.hash = bcrypt.hashpw(password.encode(
        encoding="utf-8"), bcrypt.gensalt())
    owner.save()

    send_sms(msg="Din adgangskode er blevet nulstillet",
             to=session.phone_number)

    # Remove the reset password session to prevent future access to this verified session.
    request.app.collections['2fa_sessions'].delete_one({'_id': session_id})
