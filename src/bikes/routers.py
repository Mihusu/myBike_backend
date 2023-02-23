import uuid
from fastapi import APIRouter, Body, Form, Request, Response, HTTPException, UploadFile, File, status
from fastapi.encoders import jsonable_encoder
from ..storage.aws import upload_file

from .models import Bike, BikeColor, BikeGender, BikeKind

router = APIRouter(
    tags=['bikes'], 
    prefix='/bikes'
)


@router.get('/')
def get_bike_list(request: Request) -> list[Bike]:
    bikes = list(request.app.database["bikes"].find(limit=100))
    return bikes


@router.get('/{id}', response_description="Get a single bike by id", status_code=status.HTTP_200_OK)
def get_bike_by_id(id: uuid.UUID, request: Request) -> Bike:
    bike = request.app.database["bikes"].find_one({"_id": id})
    if bike is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Bike with ID {id} not found")
    
    return bike

@router.post('/', response_description="Register a new bike", status_code=status.HTTP_201_CREATED)
def register_bike(
    request: Request, 
    frame_number: str = Form(...),
    gender: BikeGender = Form(...),
    is_electic: bool = Form(...),
    kind: BikeKind = Form(...),
    brand: str = Form(...),
    color: BikeColor = Form(...),
    images: list[UploadFile] = File(),
    #receipts: list[UploadFile] = File(),
) -> Bike:
    
    bike_info = {
        'frame_number': frame_number, 
        'gender': gender,
        'is_electic': is_electic,
        'kind': kind,
        'brand': brand,
        'color': color
    }
    
    # Handle image upload
    
    
    # @FIX: Check that bike with given frame number is not already registered
    bike = Bike(**bike_info).dict()
    
    new_bike = request.app.database["bikes"].insert_one({'_id': bike['id'], **bike})
    created_bike = request.app.database["bikes"].find_one(
        {"_id": new_bike.inserted_id}
    )

    return created_bike


@router.post('/upload', response_description="Upload test")
def upload_files(image : UploadFile = File(...)):
    
    upload_file(file=image.file, file_name=image.filename)
    
    return {"images": image}


@router.delete("/{id}", response_description="Remove a bike")
def remove_bike(id: uuid.UUID, request: Request, response: Response):
    delete_result = request.app.database["bikes"].delete_one({"_id": id})

    if delete_result.deleted_count == 1:
        response.status_code = status.HTTP_204_NO_CONTENT
        return response

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Bike with ID {id} not found")



@router.post("/claim/{claim_token}", response_description="Claim a new bike")
def claim_bike(claim_token: uuid.UUID, request: Request, response: Response):
    bike_db = request.app.database["bikes"].find_one({"claim_token": claim_token})
    bike = Bike(**bike_db)
    
    if bike.owner is None:
        if bike.state is not bike.state.CLAIMED or bike.state.REPORTED_STOLEN:
            request.app.database["bikes"].update_one({ "state" : bike.state.UNCLAIMED }, 
                                                     { "$set": { "state" : bike.state.CLAIMED } })
            response.status_code=status.HTTP_202_ACCEPTED
            return response
        
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Bike with ID {id} not found")