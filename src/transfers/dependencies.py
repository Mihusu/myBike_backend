
import uuid

from fastapi import Body, HTTPException, Request


def bike_with_id_exists(request: Request, bike_id: uuid.UUID = Body()):
    bike = request.app.collections['bikes'].find_one({'_id': bike_id})
    if not bike:
        raise HTTPException(status_code=400, detail=f"Bike with id: {bike_id} not found")
    else:
        return bike_id