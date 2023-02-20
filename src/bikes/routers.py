from fastapi import APIRouter, Body, Request, Response, HTTPException, status
from fastapi.encoders import jsonable_encoder

from src.bikes.models import BikeOwner, Bike

router = APIRouter()

example_owner = BikeOwner(
    phone_number="+4512345678",
    verified=True
)

@router.get('/', response_model=list[Bike])
def get_bike_list() -> list[Bike]:
    return [Bike(
        frame_number="12345678",
        owner=example_owner,
    )]