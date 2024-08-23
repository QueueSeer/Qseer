from typing import Annotated
from fastapi import APIRouter, Depends , File, UploadFile, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from tempfile import NamedTemporaryFile
import os

from app.database import get_session
from app.objectStorage import get_s3_connect , get_s3_main_Bucket

router = APIRouter(prefix="/test", tags=["tests"])
security = HTTPBearer(bearerFormat="test", scheme_name="JWT", description="JWT Token")


@router.get("/")
async def test():
    return [{"test": "Test"}]

@router.post("/upload")
def upload_file(file: UploadFile = File(...)):
    temp = NamedTemporaryFile(delete=False)
    try:
        try:
            contents = file.file.read()
            with temp as f:
                f.write(contents)
        except Exception:
            raise HTTPException(status_code=500, detail='Error on uploading the file')
        finally:
            file.file.close()
            
        # Upload the file to your S3 service using `temp.name`
        get_s3_connect().upload_file(temp.name, get_s3_main_Bucket() , file.filename)
        
    except Exception:
        raise HTTPException(status_code=500, detail='Something went wrong')
    finally:
        #temp.close()  # the `with` statement above takes care of closing the file
        os.remove(temp.name)  # Delete temp file
    
    #print(contents)  # Handle file contents as desired
    return {"filename": file.filename}