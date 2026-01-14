from fastapi import APIRouter
from main.services.auth import AuthRegUsersServices
from main.schemas.auth import RegistrationIn

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/", summary='Регистрация пользователя')
async def registration_users(data: RegistrationIn):
    return (await AuthRegUsersServices.registration_services(data=data))
