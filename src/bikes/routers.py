import datetime
import uuid
from fastapi import APIRouter, Depends, Form, Request, Response, HTTPException, UploadFile, File, status
from src.auth.dependencies import authenticated_request
from src.notifications.sms import send_sms
from src.storage.aws import save_file
from src.bikes.dependencies import *
from src.bikes.models import Bike, BikeColor, BikeGender, BikeKind, BikeOwner, BikeState

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

@router.get(
    '/{id}', 
    description="Get a single bike by id", 
    status_code=status.HTTP_200_OK
)
def get_bike_by_id(id: uuid.UUID, request: Request) -> Bike:
    bike = request.app.collections["bikes"].find_one({"_id": id})
    if bike is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Bike with ID {id} not found")
    
    return bike

@router.post(
    '/', 
    description="Register a new bike", 
    status_code=status.HTTP_201_CREATED, 
    dependencies=[Depends(frame_number_not_registered), Depends(valid_danish_phone_number), Depends(valid_frame_number)]
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
    
    # Need to transfer all Form fields to
    bike = Bike(
        frame_number=frame_number,
        gender= gender,
        is_electric= is_electric,
        kind= kind,
        brand= brand,
        color= color,
    )
    bike.image.upload_and_set(image)
    bike.receipt.upload_and_set(receipt)

    send_sms(
        msg=f"Hej !\nDin kode til at indløse cyklen i minCykel app'en er: \n\n{str(bike.claim_token)}", 
        to=phone_number.replace(' ','')
    )
    
    return bike.save()
    
# This feature is still questionable.
# The deletion or removal of ones own bike should probably be handled
# as a different process.
@router.delete(
    '/{id}', 
    description="Remove a bike"
)
def remove_bike(id: uuid.UUID, request: Request, response: Response):
    delete_result = request.app.collections["bikes"].delete_one({"_id": id})

    if delete_result.deleted_count == 1:
        response.status_code = status.HTTP_204_NO_CONTENT
        return response

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Bike with ID {id} not found")

@router.post("/claim/{claim_token}", description="Claim a new bike")
def claim_bike(request: Request, claim_token: uuid.UUID, user : BikeOwner = Depends(authenticated_request)) -> Bike:
    bike_in_db = request.app.collections["bikes"].find_one({"claim_token": claim_token})
    if not bike_in_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Invalid claim code")
    
    bike = Bike(**bike_in_db)
    
    if bike.owner:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Bike is already claimed")
    if bike.reported_stolen:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Bike is reported to be stolen. If you think this is a mistake, please report it to mincykel@support.dk")
    
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
    user : BikeOwner = Depends(authenticated_request)
    ) -> Bike:

    bike_in_db = request.app.collections["bikes"].find_one({"_id": id})
    bike: Bike = Bike(**bike_in_db)

    if not bike.owner == user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"User is not the bike owner")
    bike.reported_stolen = not bike.reported_stolen
    
    return bike.save()