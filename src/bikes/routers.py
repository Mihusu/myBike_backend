import datetime
import uuid
from fastapi import APIRouter, Depends, Form, Path, Request, Response, HTTPException, UploadFile, File, status
from src.auth.dependencies import authenticated_request
from src.notifications.sms import send_sms
from src.storage.aws import save_file
from src.bikes.dependencies import *
from src.bikes.models import Bike, BikeColor, BikeGender, BikeKind, BikeState, FoundBikeReport
from src.owners.models import BikeOwner


router = APIRouter(
    tags=['bikes'],
    prefix='/bikes'
)


@router.get(
    '/me',
    description="Retrieve a list of owned bikes"
)
def get_my_bikes(request: Request, user: BikeOwner = Depends(authenticated_request)) -> list[Bike]:
    bikes = list(request.app.collections["bikes"].find(
        {
            'owner': user.id
        }
    ))
    return bikes


# @router.get(
#     '/{id}',
#     description="Get a single bike by id",
#     status_code=status.HTTP_200_OK
# )
# def get_bike_by_id(id: uuid.UUID, request: Request) -> Bike:
#     bike = request.app.collections["bikes"].find_one({"_id": id})
#     if bike is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
#                             detail=f"Bike with ID {id} not found")

#     return bike

@router.get(
    '/{frame_number}',
    description="Get info about if a bike has been reported stolen",
    status_code=status.HTTP_200_OK
)
def get_bike_by_frame_number(request: Request, frame_number: str, user: BikeOwner = Depends(authenticated_request)) -> Bike:
    bike_in_db = request.app.collections["bikes"].find_one(
        {"frame_number": frame_number.lower()})
    if bike_in_db is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Cykel med stelnummer {frame_number} ikke fundet i vores system")
    bike = Bike(**bike_in_db)

    if bike.reported_stolen:
        return bike
    else:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    '/discoveries',
    description="Report a found bike",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(authenticated_request)]
)
def found_bike_report(
    bike_owner: uuid.UUID = Form(...),
    frame_number: str = Form(...),
    address: str = Form(...),
    comment: str = Form(...),
    image: UploadFile = File(default=None),

) -> FoundBikeReport:

 # Need to transfer all Form fields to
    bikeIncident = FoundBikeReport(
        bike_owner=bike_owner,
        address=address,
        comment=comment,
        frame_number=frame_number.lower(),
    )
    bikeIncident.image.upload_and_set(image)

    return bikeIncident.save()


@router.post(
    '',
    description="Register a new bike",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(frame_number_not_registered), Depends(
        valid_danish_phone_number), Depends(valid_frame_number)]
)
def register_bike(
    phone_number: str = Form(...),
    frame_number: str = Form(...),
    gender: BikeGender = Form(...),
    is_electric: bool = Form(...),
    kind: BikeKind = Form(...),
    brand: str = Form(...),
    color: BikeColor = Form(...),
    image: UploadFile = File(default=None),
    receipt: UploadFile = File(default=None)
) -> Bike:

    # No matter how the user inputs the frame number,
    # we handle that serverside and save as lower case
    # Need to transfer all Form fields to bike model
    bike = Bike(
        frame_number=frame_number.lower(),
        gender=gender,
        is_electric=is_electric,
        kind=kind,
        brand=brand,
        color=color,
    )
    bike.image.upload_and_set(image)
    bike.receipt.upload_and_set(receipt)

    send_sms(
        msg=f"Hej !\nDin kode til at indløse cyklen i minCykel app'en er: \n\n{str(bike.claim_token)}",
        to=phone_number.replace(' ', '')
    )

    return bike.save()

@router.post("/claim/{claim_token}", description="Claim a new bike")
def claim_bike(request: Request, claim_token: uuid.UUID, user: BikeOwner = Depends(authenticated_request)) -> Bike:
    bike_in_db = request.app.collections["bikes"].find_one(
        {"claim_token": claim_token})
    if not bike_in_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Invalid claim code")

    bike = Bike(**bike_in_db)

    if bike.owner:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Bike is already claimed")
    if bike.reported_stolen:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Bike is reported to be stolen. If you think this is a mistake, please report it to mincykel@support.dk")

    # This hands over the ownership to the sender of the request
    bike.owner = user.id
    bike.state = BikeState.TRANSFERABLE
    bike.claimed_date = datetime.datetime.now()
    bike.save()

    return bike


@router.put(
    '/{id}/reportstolen',
    description="Report a bike stolen or found",
    status_code=status.HTTP_200_OK
)
def report_bike_stolen(
    id: uuid.UUID,
    request: Request,
    user: BikeOwner = Depends(authenticated_request)
):

    bike_in_db = request.app.collections["bikes"].find_one({"_id": id})
    bike: Bike = Bike(**bike_in_db)

    if not bike.owner == user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"User is not the bike owner")
    
    # If correct owner, flip bike's stolen attribute
    bike.reported_stolen = not bike.reported_stolen

    # If reported found, remove any existing discoveries pertaining to this bike
    if not bike.reported_stolen:
        request.app.collections["discoveries"].delete_many({"frame_number": bike.frame_number})

    bike.save()
