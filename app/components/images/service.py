from app.objectStorage import get_s3_connect , get_s3_main_Bucket
from app.core.config import settings
from fastapi import APIRouter, Depends , File, UploadFile, HTTPException
import urllib.parse

custom_url = "https://storage.qseer.app/"

def CreateUrl(part_name : str,file_name :str):
    return custom_url + urllib.parse.quote(part_name+"/"+file_name)

async def UploadImage(part_name : str,file_name :str,file: UploadFile = File(...)):
    try:
        get_s3_connect().upload_fileobj(file.file, get_s3_main_Bucket(), part_name+"/"+file_name)
    except Exception:
        return False
    return True

async def DeleteImage(part_name : str,file_name :str):
    try:
        get_s3_connect().delete_object(Bucket=get_s3_main_Bucket(), Key=part_name+"/"+file_name)
    except Exception:
        return False
    return True

async def Delete_User_Image(user_id : int):
    try:
        await DeleteImage("user",str(user_id))
    except Exception:
        return False
    return True