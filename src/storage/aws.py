import datetime
import logging
import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException, UploadFile

from src.settings import config

s3_client = boto3.client(
    service_name='s3',
    aws_access_key_id=config['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=config['AWS_SECRET_ACCESS_KEY'],
    region_name=config['AWS_DEFAULT_REGION']
)

def save_file(file: UploadFile):
    
    object_name = str(datetime.datetime.now()) + file.filename

    try:
        s3_client.upload_fileobj(file.file, config['AWS_BUCKET_NAME'], object_name)
        return object_name
            
    except ClientError as e:
        logging.error(e)
        raise HTTPException(status_code=500, detail=f"Error: Failed to save file {file.filename}")