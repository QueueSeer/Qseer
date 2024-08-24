from typing import Annotated
from fastapi import APIRouter, Depends , File, UploadFile, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
import urllib.parse
import os

from app.database import get_session
from app.objectStorage import get_s3_connect , get_s3_main_Bucket
from app.core.config import settings

router = APIRouter(prefix="/test", tags=["tests"])
security = HTTPBearer(bearerFormat="test", scheme_name="JWT", description="JWT Token")


@router.get("/",deprecated=not settings.DEVELOPMENT)
async def test():
    if settings.DEVELOPMENT == False :
        raise HTTPException(status_code=503, detail='only available on dev server')
    
    return [{"test": "Test"}]

@router.post("/upload",deprecated=not settings.DEVELOPMENT)
async def upload_file(file: UploadFile = File(...)):
    if settings.DEVELOPMENT == False :
        raise HTTPException(status_code=503, detail='only available on dev server')
    
    try:
        get_s3_connect().upload_fileobj(file.file, get_s3_main_Bucket(), file.filename)
    except Exception:
        raise HTTPException(status_code=500, detail='Something went wrong')
    custom_url = "https://storage.qseer.app/"
    return [{"filename": file.filename},{"fileType":file.content_type},{"url": custom_url + urllib.parse.quote(file.filename)}]

@router.get("/get_url",deprecated=not settings.DEVELOPMENT)
async def get_url(file_name:str):
    if settings.DEVELOPMENT == False :
        raise HTTPException(status_code=503, detail='only available on dev server')
    custom_url = "https://storage.qseer.app/"
    return [{"url": custom_url + urllib.parse.quote(file_name)}]