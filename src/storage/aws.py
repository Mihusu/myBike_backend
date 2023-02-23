import logging
from typing import BinaryIO
from dotenv import dotenv_values
import boto3
from botocore.exceptions import ClientError
import os

config = dotenv_values(".env")

s3_client = boto3.client(
    service_name='s3',
    aws_access_key_id=config['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=config['AWS_SECRET_ACCESS_KEY'],
    region_name=config['AWS_DEFAULT_REGION']
)

def upload_file(file: BinaryIO, file_name: str, object_name=None):
    """Upload a file to S3 bucket
    :param file: File in bytes form
    :param file_name: Filename of the file to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """
    BUCKET_NAME = config['AWS_BUCKET_NAME']
    
    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    try:
        response = s3_client.upload_fileobj(file, BUCKET_NAME, object_name)
        print(response)
            
    except ClientError as e:
        logging.error(e)
        return False
    return True