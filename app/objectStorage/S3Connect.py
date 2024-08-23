from dataplane import s3_upload
import os
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import json
import os, sys
from PIL import Image


load_dotenv()
AccountID = os.environ["secret_dp_S3_ACCOUNT_ID"]
Bucket = os.environ["main_BUCKET_NAME"]
ClientAccessKey = os.environ["secret_dp_S3_ACCESS_KEY"]
ClientSecret = os.environ["secret_dp_S3_SECRET"]
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