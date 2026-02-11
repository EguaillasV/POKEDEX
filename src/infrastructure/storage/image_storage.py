"""
Image Storage Adapter
Handles image storage locally or in cloud (S3).
"""
import os
import uuid
import logging
from typing import Optional
from django.conf import settings

from src.domain.value_objects import ImageFrame
from src.domain.ports import ImageStoragePort
from src.domain.exceptions import StorageException

logger = logging.getLogger(__name__)


class LocalImageStorage(ImageStoragePort):
    """
    Local filesystem implementation of ImageStoragePort.
    Stores images in the media directory.
    """
    
    def __init__(self, base_path: Optional[str] = None):
        self._base_path = base_path or os.path.join(settings.MEDIA_ROOT, 'thumbnails')
        os.makedirs(self._base_path, exist_ok=True)
    
    def save_thumbnail(self, image: ImageFrame, filename: str) -> str:
        """Save a thumbnail and return its URL"""
        try:
            filepath = os.path.join(self._base_path, filename)
            
            # Verificar que image.data no esté vacío
            if not image.data:
                logger.warning(f"⚠️ save_thumbnail: image.data está vacío para {filename}")
            
            # Escribir el archivo
            with open(filepath, 'wb') as f:
                bytes_written = f.write(image.data)
                logger.info(f"✓ save_thumbnail: Guardado {filename} ({bytes_written} bytes) en {filepath}")
            
            # Verificar que el archivo existe después de escribir
            if os.path.exists(filepath):
                logger.info(f"✓ save_thumbnail: Archivo verificado, existe en disco")
            else:
                logger.error(f"❌ save_thumbnail: Archivo NO existe después de escribir!")
            
            # Return relative URL
            url = f"{settings.MEDIA_URL}thumbnails/{filename}"
            logger.info(f"✓ save_thumbnail: Devolviendo URL: {url}")
            return url
            
        except Exception as e:
            logger.error(f"❌ save_thumbnail ERROR: {str(e)}")
            raise StorageException(f"Failed to save thumbnail: {str(e)}")
    
    def get_thumbnail_url(self, filename: str) -> str:
        """Get the URL for a thumbnail"""
        return f"{settings.MEDIA_URL}thumbnails/{filename}"
    
    def delete_thumbnail(self, filename: str) -> bool:
        """Delete a thumbnail"""
        try:
            filepath = os.path.join(self._base_path, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete thumbnail: {str(e)}")
            return False


class S3ImageStorage(ImageStoragePort):
    """
    AWS S3 implementation of ImageStoragePort.
    Stores images in an S3 bucket.
    """
    
    def __init__(
        self,
        bucket_name: Optional[str] = None,
        region: Optional[str] = None
    ):
        import boto3
        
        self._bucket_name = bucket_name or os.getenv('AWS_STORAGE_BUCKET_NAME')
        self._region = region or os.getenv('AWS_S3_REGION_NAME', 'us-east-1')
        
        self._s3_client = boto3.client(
            's3',
            region_name=self._region,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        )
        
        self._base_path = 'thumbnails'
    
    def save_thumbnail(self, image: ImageFrame, filename: str) -> str:
        """Save a thumbnail to S3 and return its URL"""
        try:
            key = f"{self._base_path}/{filename}"
            
            self._s3_client.put_object(
                Bucket=self._bucket_name,
                Key=key,
                Body=image.data,
                ContentType=f'image/{image.format}',
            )
            
            # Return public URL
            return f"https://{self._bucket_name}.s3.{self._region}.amazonaws.com/{key}"
            
        except Exception as e:
            raise StorageException(f"Failed to save thumbnail to S3: {str(e)}")
    
    def get_thumbnail_url(self, filename: str) -> str:
        """Get the URL for a thumbnail"""
        key = f"{self._base_path}/{filename}"
        return f"https://{self._bucket_name}.s3.{self._region}.amazonaws.com/{key}"
    
    def delete_thumbnail(self, filename: str) -> bool:
        """Delete a thumbnail from S3"""
        try:
            key = f"{self._base_path}/{filename}"
            self._s3_client.delete_object(
                Bucket=self._bucket_name,
                Key=key,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete thumbnail from S3: {str(e)}")
            return False


def get_image_storage() -> ImageStoragePort:
    """Factory function to get the appropriate storage adapter"""
    use_s3 = os.getenv('USE_S3_STORAGE', 'False').lower() == 'true'
    
    if use_s3:
        return S3ImageStorage()
    else:
        return LocalImageStorage()
