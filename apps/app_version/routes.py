from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
import os
import uuid
from pathlib import Path
from fastapi import UploadFile, File

from apps.app_version.models import App, Version
from apps.app_version.schemas import (
    AppCreate,
    AppUpdate,
    AppResponse,
    VersionCreate,
    VersionUpdate,
    VersionResponse,
)
from config.database import get_async_session
from apps.user.di import get_current_user_by_token
from apps.user.models import User, UserType

router = APIRouter(
    prefix="/apps",
    tags=["App-Version Management"],
)


# --- APP CRUD ---

@router.post("/", response_model=AppResponse, status_code=status.HTTP_201_CREATED)
async def create_app(
    app_data: AppCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    # Only superadmin or admin can create apps
    if current_user.user_type not in [UserType.SUPERADMIN, UserType.ADMIN]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    result = await session.execute(select(App).where(App.name.ilike(f"%{app_data.name}%")))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="App with this name already exists")
    
    new_app = App(**app_data.model_dump())
    session.add(new_app)
    await session.commit()
    await session.refresh(new_app)
    return new_app


@router.get("/", response_model=list[AppResponse])
async def list_apps(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    result = await session.execute(select(App))
    return result.scalars().all()


@router.get("/{app_id}", response_model=AppResponse)
async def get_app(
    app_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    result = await session.execute(select(App).where(App.id == app_id))
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="App not found")
    return app


@router.put("/{app_id}", response_model=AppResponse)
async def update_app(
    app_id: int,
    app_update: AppUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    if current_user.user_type not in [UserType.SUPERADMIN, UserType.ADMIN]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    result = await session.execute(select(App).where(App.id == app_id))
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="App not found")
    
    update_data = app_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(app, field, value)
    
    await session.commit()
    await session.refresh(app)
    return app


@router.delete("/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_app(
    app_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    if current_user.user_type != UserType.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Only superadmin can delete apps")
    
    result = await session.execute(select(App).where(App.id == app_id))
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="App not found")
    
    await session.delete(app)
    await session.commit()


# --- VERSION CRUD ---

@router.post("/{app_id}/versions", response_model=VersionResponse, status_code=status.HTTP_201_CREATED)
async def create_version(
    app_id: int,
    version_data: VersionCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    if current_user.user_type not in [UserType.SUPERADMIN, UserType.ADMIN]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Verify app exists
    result = await session.execute(select(App).where(App.id == app_id))
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="App not found")
    
    # Ensure version_data.app_id matches path
    if version_data.app_id != app_id:
        raise HTTPException(status_code=400, detail="App ID mismatch")
    
    new_version = Version(**version_data.model_dump())
    session.add(new_version)
    await session.commit()
    await session.refresh(new_version)
    return new_version


@router.get("/{app_id}/versions", response_model=list[VersionResponse])
async def list_versions(
    app_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    result = await session.execute(select(Version).where(Version.app_id == app_id).order_by(desc(Version.created_at)))
    return result.scalars().all()


@router.get("/versions/{version_id}", response_model=VersionResponse)
async def get_version(
    version_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    result = await session.execute(select(Version).where(Version.id == version_id))
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    return version


@router.put("/versions/{version_id}", response_model=VersionResponse)
async def update_version(
    version_id: int,
    version_update: VersionUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    if current_user.user_type not in [UserType.SUPERADMIN, UserType.ADMIN]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    result = await session.execute(select(Version).where(Version.id == version_id))
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    update_data = version_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(version, field, value)
    
    await session.commit()
    await session.refresh(version)
    return version


@router.delete("/versions/{version_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_version(
    version_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    if current_user.user_type != UserType.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Only superadmin can delete versions")
    
    result = await session.execute(select(Version).where(Version.id == version_id))
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    await session.delete(version)
    await session.commit()


# Keep existing endpoints
@router.get("/latest-version", response_model=VersionResponse)
async def get_latest_version(
    app_type: str = Query(..., description="App type (e.g., agent, deliverer)"),
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(select(App).where(App.name.ilike(f"%{app_type}%")))
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(
            status_code=404, detail=f"App with type '{app_type}' not found"
        )

    result = await session.execute(
        select(Version)
        .where(Version.app_id == app.id)
        .order_by(desc(Version.created_at))
        .limit(1)
    )
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(
            status_code=404, detail="No version found for this app"
        )

    return version


# Define upload directory (relative to your project root)
UPLOAD_DIR = Path("static/uploads/apps")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload-apk", tags=["File Management"])
async def upload_apk_file(file: UploadFile = File(...)):
    # 1. Sanitize and get the original filename
    original_filename = os.path.basename(file.filename)

    # 2. Validate file extension
    extension = os.path.splitext(original_filename)[1].lower()
    if extension not in [".apk", ".ipa", ".exe"]:
        raise HTTPException(
            status_code=400,
            detail="Only app binaries (.apk, .ipa, .exe) are allowed"
        )

    # 3. Define the local path using the original name
    file_path = UPLOAD_DIR / original_filename

    # 4. Check if file already exists
    if file_path.exists():
        raise HTTPException(
            status_code=409,
            detail="A file with this name already exists. Please rename your file."
        )

    # 5. Save the file locally
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Could not save file: {str(e)}")

    # 6. Return the access URL
    relative_url = f"/static/uploads/apps/{original_filename}"

    return {
        "filename": original_filename,
        "url": relative_url,
        "size": len(content)
    }
