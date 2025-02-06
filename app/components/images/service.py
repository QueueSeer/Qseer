from fastapi import UploadFile
import urllib.parse

from app.objectStorage import get_s3_connect, get_s3_main_Bucket
from app.core.config import settings
from app.core.error import BadRequestException

custom_url = "https://storage.qseer.app/"

ALLOWED_EXTENSIONS = {"image/png", "image/jpeg"}
MAX_FILE_SIZE_MB = 10  # MB


async def ValidateFile(file: UploadFile):
    if file.content_type not in ALLOWED_EXTENSIONS:
        raise BadRequestException("Only PNG and JPG files are allowed.")

    if file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise BadRequestException(
            f"File too large. Max size is {MAX_FILE_SIZE_MB} MB."
        )
    return True


def CreateUrl(part_name: str, file_name: str):
    return custom_url + urllib.parse.quote(part_name+"/"+file_name)


async def UploadImage(part_name: str, file_name: str, file: UploadFile):
    try:
        get_s3_connect().upload_fileobj(
            file.file, get_s3_main_Bucket(), part_name+"/"+file_name)
    except Exception:
        return False
    return True


async def DeleteImage(part_name: str, file_name: str):
    try:
        get_s3_connect().delete_object(
            Bucket=get_s3_main_Bucket(),
            Key=part_name+"/"+file_name
        )
    except Exception:
        return False
    return True


async def delete_user_profile_image(user_id: int):
    '''
    Only Delete at R2 Object Storage :3
    '''
    return await DeleteImage("user", str(user_id))


async def delete_fortune_package_image(seer_id: int, package_id: int):
    '''
    Only Delete at R2 Object Storage :3
    '''
    return await DeleteImage("package/fortune", str(seer_id)+"-"+str(package_id))


async def delete_question_package_image(seer_id: int):
    '''
    Only Delete at R2 Object Storage :3
    '''
    return await DeleteImage("package/question", str(seer_id)+"-"+str(1))
