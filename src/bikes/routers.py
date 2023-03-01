import uuid
from fastapi import APIRouter, Depends, Form, Request, Response, HTTPException, UploadFile, File, status
from src.notifications.sms import send_sms
from src.storage.aws import save_file
from src.bikes.dependencies import *
from src.bikes.models import Bike, BikeColor, BikeGender, BikeKind



router = APIRouter(
    tags=['bikes'], 
    prefix='/bikes'
)


@router.get('/')
def get_bike_list(request: Request) -> list[Bike]:
    bikes = list(request.app.collections["bikes"].find(limit=100))
    return bikes


@router.get('/{id}', response_description="Get a single bike by id", status_code=status.HTTP_200_OK)
def get_bike_by_id(id: uuid.UUID, request: Request) -> Bike:
    bike = request.app.collections["bikes"].find_one({"_id": id})
    if bike is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Bike with ID {id} not found")
    
    return bike


@router.post('/', 
             response_description="Register a new bike", 
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
    images: list[UploadFile] = File(default=[]),
    receipts: list[UploadFile] = File(default=[])
) -> Bike:
    
    bike_info = {
        'frame_number': frame_number, 
        'gender': gender,
        'is_electric': is_electric,
        'kind': kind,
        'brand': brand,
        'color': color,
        'images': [save_file(image) for image in images if images],
        'receipts': [save_file(receipt) for receipt in receipts if receipts]
    }

    bike = Bike(**bike_info)

    # Sending two sms messages so to allow for easy copying of the long claim token on phones.
    send_sms(
        msg=f"Hej !\nDin kode til at indløse cyklen i minCykel app'en er: \n\n{str(bike.claim_token)}", 
        to=phone_number.replace(' ','')
    )
    
    return bike.save()
    

@router.delete("/{id}", response_description="Remove a bike")
def remove_bike(id: uuid.UUID, request: Request, response: Response):
    delete_result = request.app.collections["bikes"].delete_one({"_id": id})

    if delete_result.deleted_count == 1:
        response.status_code = status.HTTP_204_NO_CONTENT
        return response

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Bike with ID {id} not found")



@router.post("/claim/{claim_token}", response_description="Claim a new bike")
def claim_bike(claim_token: uuid.UUID, request: Request, response: Response):
    bike_db = request.app.collections["bikes"].find_one({"claim_token": claim_token})
    bike = Bike(**bike_db)
    
    if bike.owner is None:
        if bike.state is not bike.state.CLAIMED or bike.state.REPORTED_STOLEN:
            request.app.collections["bikes"].update_one({ "state" : bike.state.UNCLAIMED }, 
                                                     { "$set": { "state" : bike.state.CLAIMED } })
            response.status_code=status.HTTP_202_ACCEPTED
            return response
        
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Bike with ID {id} not found")