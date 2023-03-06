"""
    Main routers file
    
    To add a new router to the app:
        1. Add the router import
        2. Add it to the main router
"""

from fastapi import APIRouter

from src.bikes.routers import router as bike_router
from src.auth.routers import router as auth_router
from src.notifications.routers import router as notification_router


main_router = APIRouter()


main_router.include_router(bike_router)
main_router.include_router(auth_router)
main_router.include_router(notification_router)
