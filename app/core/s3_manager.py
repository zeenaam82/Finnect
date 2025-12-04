import boto3
from io import BytesIO
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class S3Manager:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY,
            aws_secret_access_key=settings.AWS_SECRET_KEY,
            region_name=settings.REGION
        )
        self.bucket = settings.BUCKET_NAME

    def upload_fileobj(self, file_obj, folder: str, filename: str) -> str:
        """파일 객체(스트림)를 S3에 직접 업로드"""
        try:
            s3_key = f"{folder}/{filename}"
            if hasattr(file_obj, 'seek'):
                file_obj.seek(0)
            
            self.s3_client.upload_fileobj(file_obj, self.bucket, s3_key)
            logger.info(f"S3 Upload Success: {s3_key}")
            return s3_key
        except Exception as e:
            logger.error(f"S3 Upload Failed: {e}")
            raise e

    def read_file(self, s3_key: str) -> BytesIO:
        """S3에서 파일을 읽어 BytesIO 객체로 반환"""
        try:
            obj = self.s3_client.get_object(Bucket=self.bucket, Key=s3_key)
            return BytesIO(obj['Body'].read())
        except Exception as e:
            logger.error(f"S3 Read Failed: {e}")
            raise e

    def download_file(self, s3_key: str, local_path: str):
        """S3 객체를 지정된 로컬 경로에 다운로드"""
        try:
            self.s3_client.download_file(self.bucket, s3_key, local_path)
            logger.info(f"S3 Download Success: {s3_key} -> {local_path}")
        except Exception as e:
            logger.error(f"S3 Download Failed for {s3_key}: {e}")
            raise e
    
    def upload_file(self, local_path: str, bucket_name: str, s3_key: str):
        """로컬 경로의 파일을 S3의 지정된 키로 업로드"""
        try:
            # upload_fileobj와 달리, local_path를 직접 받아 업로드
            self.s3_client.upload_file(local_path, bucket_name, s3_key)
            logger.info(f"S3 Upload Success: {local_path} -> {s3_key}")
        except Exception as e:
            logger.error(f"S3 Upload Failed for {local_path} to {s3_key}: {e}")
            raise e

    def delete_file(self, s3_key: str):
        """S3에서 지정된 키의 객체를 삭제"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=s3_key)
            logger.info(f"S3 Delete Success: {s3_key}")
        except Exception as e:
            logger.error(f"S3 Delete Failed for {s3_key}: {e}")
            raise e

s3_manager = S3Manager()