from fastapi import Form, HTTPException, Request


def frame_number_not_registered(request: Request, frame_number: str = Form(...)):
    bike = request.app.collections['bikes'].find_one({'frame_number': frame_number})
    if bike:
        raise HTTPException(status_code=400, detail=f"Bike with frame number '{frame_number}' is already registered")
