import uuid

from fastapi import Body, HTTPException, Request


def bike_with_id_exists(request: Request, bike_id: uuid.UUID = Body()):
    bike = request.app.collections['bikes'].find_one({'_id': bike_id})
    if not bike:
        raise HTTPException(status_code=400, detail=f"Bike with id: {bike_id} not found")
    else:
        return bike_id
    
def transfer_with_id_exists(request: Request, transfer_id: uuid.UUID = Body()):
    transfer = request.app.collections['transfers'].find_one({'_id': transfer_id})
    if not transfer:
        raise HTTPException(status_code=400, detail=f"Transfer with id: {transfer_id} not found")
    else:
        return transfer_id