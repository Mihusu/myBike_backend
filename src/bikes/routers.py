from fastapi import APIRouter, Body, Request, Response, HTTPException, status
from fastapi.encoders import jsonable_encoder

from src.bikes.models import BikeOwner, Bike, BikeRegistrationInfo

router = APIRouter(
    tags=['bikes'], 
    prefix='/bikes'
)

example_owner = BikeOwner(
    phone_number="+4512345678",
    verified=True
)


@router.get('/')
def get_bike_list(request: Request) -> list[Bike]:
    bikes = list(request.app.database["bikes"].find(limit=100))
    return bikes


@router.get('/{id}', response_description="Get a single bike by id", status_code=status.HTTP_200_OK)
def get_bike_by_id(id: str, request: Request) -> Bike:
    bike = request.app.database["bikes"].find_one({"_id": id})
    if bike is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Bike with ID {id} not found")
    
    return bike


@router.post('/', response_description="Register a new bike", status_code=status.HTTP_201_CREATED)
def register_bike(request: Request, bike_info: BikeRegistrationInfo = Body(...)) -> Bike:
    
    # @FIX: Check that bike with given frame number is not already registered
    bike_info = jsonable_encoder(bike_info)
    bike = Bike(**bike_info).dict()
    
    new_bike = request.app.database["bikes"].insert_one({'_id': bike['id'], **bike})
    created_bike = request.app.database["bikes"].find_one(
        {"_id": new_bike.inserted_id}
    )

    return created_bike


@router.delete("/{id}", response_description="Remove a bike")
def remove_bike(id: str, request: Request, response: Response):
    delete_result = request.app.database["bikes"].delete_one({"_id": id})

    if delete_result.deleted_count == 1:
        response.status_code = status.HTTP_204_NO_CONTENT
        return response

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Bike with ID {id} not found")


