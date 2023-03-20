import datetime
import logging
from typing import Self
import uuid
import boto3
from dotenv import dotenv_values
from fastapi import HTTPException, UploadFile
from pydantic import BaseModel, Field, PrivateAttr
from botocore.exceptions import ClientError

from src.models import Entity


config = dotenv_values(".env")

s3_client = boto3.client(
    service_name='s3',
    aws_access_key_id=config['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=config['AWS_SECRET_ACCESS_KEY'],
    region_name=config['AWS_DEFAULT_REGION']
)


class S3File(BaseModel):
    _path                    : str           # Path at where to save the given file on aws. Ex "images" would put the file at '/images/FILE' in s3
    _allowed_content_types   : list[str]     # Ex. ['image/png', 'application/pdf'] etc
    _max_size                : int | None    # Optional max size of file in bytes

    content_type            : str | None
    size                    : int | None
    filename                : str | None
    obj_name                : str | None    # Name of the full path in s3. Should not be set directly !
    obj_url                 : str | None    

    @classmethod
    def field(cls, path: str, allowed_content_types: list[str], max_size: int | None = None) -> Self:
        s3f = S3File()
        s3f._path = path
        s3f._allowed_content_types = allowed_content_types
        s3f._max_size = max_size
        return s3f

    def upload_and_set(self, file: UploadFile):
        if not file:
            return
        if not '*' in self._allowed_content_types:
            if not file.content_type in self._allowed_content_types:
                raise HTTPException(status_code=400, detail=f"Invalid content type for file '{file.filename}'. Valid content types include: {self._allowed_content_types}")
        if self._max_size:
            if file.size > self._max_size:
                raise HTTPException(status_code=400, detail=f"File size too large. Allowed file size is: {self._max_size // 1000}KB")
        
        # Save info to object
        file_obj_name = f"{self._path}/{uuid.uuid4()}{file.filename}"

        self.content_type = file.content_type
        self.size         = file.size
        self.filename     = file.filename
        self.obj_name     = file_obj_name
        self.obj_url      = f"https://{config['AWS_BUCKET_NAME']}.s3.{config['AWS_DEFAULT_REGION']}.amazonaws.com/{self.obj_name}"

        # Everything is fine. Begin upload to s3
        try:
            s3_client.upload_fileobj(file.file, config['AWS_BUCKET_NAME'], file_obj_name)
            
        except ClientError as e:
            logging.error(e)
            raise HTTPException(status_code=500, detail=f"{datetime.datetime.now()}: Failed to save file {file.filename}")
    
    class Config:
        underscore_attrs_are_private = True
    
