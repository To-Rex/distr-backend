from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import exc, select
from starlette import status

from apps.user import schemas
from apps.user.authentication import authenticate, create_access_token, create_jwt_tokens
from apps.user.di import get_current_user, get_current_user_by_token
from apps.user.jwt_handler import verify_refresh_token
from apps.user.models import User, UserStatus, UserType
from apps.user.schemas import LoginRequest, TokenResponse, UserCreate, JwtTokenResponse, RefreshTokenRequest
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


@router.post("/login-legacy", response_model=TokenResponse)
async def login_legacy(
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
            "uz": f"Foydalanuvchi tizimga kirdi (legacy) {user.username}",
            "ru": f"Пользователь вошел в систему (legacy) {user.username}",
            "en": f"User logged in (legacy) {user.username}",
        })
        return token

    except HTTPException as e:
        print("Authentication failed for user:", e)
        raise
    except Exception as e:
        print("Unexpected error occurred:",     e)
        await session.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")



@router.post("/login", response_model=JwtTokenResponse)
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

        tokens = await create_jwt_tokens(user, session)
        ActivityService.log("user_login", {
            "uz": f"Foydalanuvchi tizimga kirdi {user.username}",
            "ru": f"Пользователь вошел в систему {user.username}",
            "en": f"User logged in {user.username}",
        })
        return tokens

    except HTTPException as e:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/refresh-token", response_model=JwtTokenResponse)
async def refresh_token_endpoint(
        refresh_request: RefreshTokenRequest,
        session: AsyncSession = Depends(get_async_session)
):
    try:
        payload = verify_refresh_token(refresh_request.refresh_token)
        if payload is None:
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

        user_id = int(payload["sub"])
        query = select(User).where(User.id == user_id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        if user.user_status == UserStatus.BLOCKED:
            raise HTTPException(status_code=400, detail="Account is not active")

        tokens = await create_jwt_tokens(user, session)
        ActivityService.log("user_login", {
            "uz": f"Foydalanuvchi token yangiladi (JWT) {user.username}",
            "ru": f"Пользователь обновил токен (JWT) {user.username}",
            "en": f"User refreshed token (JWT) {user.username}",
        })
        return tokens
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")


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
