import boto3
from botocore.client import Config
from app.core.config import settings
import os

AccountID = settings.secret_dp_S3_ACCOUNT_ID
Bucket = settings.main_BUCKET_NAME
ClientAccessKey = settings.secret_dp_S3_ACCESS_KEY
ClientSecret = settings.secret_dp_S3_SECRET
ConnectionUrl = f"https://{AccountID}.r2.cloudflarestorage.com"


# Create a client to connect to Cloudflare's R2 Storage
S3Connect = boto3.client(
    's3',
    endpoint_url=ConnectionUrl,
    aws_access_key_id=ClientAccessKey,
    aws_secret_access_key=ClientSecret,
    config=Config(signature_version='s3v4'),
    region_name='auto'

)
def get_s3_connect():
    return S3Connect

def get_s3_main_Bucket():
    return Bucket