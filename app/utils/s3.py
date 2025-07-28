import boto3
import logging
from app.config import settings

logger = logging.getLogger(__name__)

s3 = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
)

def upload_to_s3(file_path, s3_key):
    logger.info(f"Uploading file to S3: {file_path}")
    logger.info(f"S3 key: {s3_key}")
    logger.info(f"S3 bucket: {settings.AWS_S3_BUCKET}")
    
    try:
        s3.upload_file(file_path, settings.AWS_S3_BUCKET, s3_key)
        url = f"https://{settings.AWS_S3_BUCKET}.s3.amazonaws.com/{s3_key}"
        logger.info(f"File uploaded successfully to: {url}")
        return url
    except Exception as e:
        error_msg = f"S3 upload failed: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg) 