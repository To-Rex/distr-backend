from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import exc
from starlette import status

from apps.user import schemas
from apps.user.authentication import authenticate, create_access_token, authenticate_without_fcm_token
from apps.user.di import get_current_user, get_current_user_by_token
from apps.user.models import User, UserStatus, UserType
from apps.user.schemas import LoginRequest, TokenResponse, UserCreate
from apps.activity.services.activity_service import ActivityService
from config.database import get_async_session
from config.security import get_password_hash

router = APIRouter(
    prefix="/authentication",
    tags=["Authentication"],
)


@router.post(
    "/register", status_code=status.HTTP_201_CREATED,
    response_model=schemas.UserRead
)
async def register(
        user_create: UserCreate,
        session: AsyncSession = Depends(get_async_session)
):
    try:
        username = user_create.username
        password = user_create.password
        user = User(
            username=username,
            email=user_create.email,
            password=get_password_hash(password),
            user_type=UserType.ADMIN,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        ActivityService.log("user_registered", {
            "uz": f"Foydalanuvchi ro'yxatdan o'tdi {user.username}",
            "ru": f"Пользователь зарегистрирован {user.username}",
            "en": f"User registered {user.username}",
        })
        return user
    except exc.IntegrityError as e:
        print(e)
        await session.rollback()
        raise HTTPException(status_code=400, detail="Username already exists")
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(
        login_request: LoginRequest,
        session: AsyncSession = Depends(get_async_session)
):
    try:
        username = login_request.email
        password = login_request.password
        fcm_token = login_request.firebase_token
        user = await authenticate(username, password, fcm_token, session)
        if user is None:
            raise HTTPException(
                status_code=401, detail="Incorrect username or password"
            )
        if user.user_status == UserStatus.BLOCKED:
            raise HTTPException(
                status_code=400, detail="Account is not active"
            )

        token = await create_access_token(user, session)
        ActivityService.log("user_login", {
            "uz": f"Foydalanuvchi tizimga kirdi {user.username}",
            "ru": f"Пользователь вошел в систему {user.username}",
            "en": f"User logged in {user.username}",
        })
        return token

    except HTTPException as e:
        print("Authentication failed for user:", e)
        raise
    except Exception as e:
        print("Unexpected error occurred:",     e)
        await session.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/create-token")
async def create_token(
        form_date: OAuth2PasswordRequestForm = Depends(
            OAuth2PasswordRequestForm),
        session: AsyncSession = Depends(get_async_session)
):
    try:
        username = form_date.username
        password = form_date.password
        user = await authenticate_without_fcm_token(username, password, session)
        if user is None:
            raise HTTPException(
                status_code=400, detail="Incorrect username or password")
        if user.user_status == UserStatus.BLOCKED:
            raise HTTPException(
                status_code=400, detail="Account is not active"
            )
        token = await create_access_token(user, session)
        return {
            "access_token": token.access_token,
        }
    except HTTPException:
        raise
    except Exception as e:
        print(e)
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/profile", response_model=schemas.UserResponse)
async def get_user_profile(
        current_user: User = Depends(get_current_user_by_token)
):
    """
    Get the profile of the currently authenticated user.
    """
    return current_user


@router.get("/logout")
async def logout():
    pass
