from typing import Annotated
from fastapi import APIRouter, Depends , File, UploadFile, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from tempfile import NamedTemporaryFile
import os

from app.database import get_session
from app.objectStorage import get_s3_connect , get_s3_main_Bucket
from app.core.config import settings

router = APIRouter(prefix="/test", tags=["tests"])
security = HTTPBearer(bearerFormat="test", scheme_name="JWT", description="JWT Token")


@router.get("/",deprecated=not settings.DEVELOPMENT)
async def test():
    return [{"test": "Test"}]

@router.post("/upload",deprecated=not settings.DEVELOPMENT)
def upload_file(file: UploadFile = File(...)):
    temp = NamedTemporaryFile(delete=False)
    try:
        contents = file.file.read()
        file.file.seek(0)
        get_s3_connect().upload_fileobj(file.file, get_s3_main_Bucket(), file.filename)
    except Exception:
        raise HTTPException(status_code=500, detail='Something went wrong')
    finally:
        file.file.close()

    return [{"filename": file.filename},{"fileType":file.content_type}]