"""Cloudinary service for image uploads"""

import cloudinary
import cloudinary.uploader
import cloudinary.api
import os
import logging
from typing import Optional, Dict, Any
import base64
from io import BytesIO

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Maximum file size in bytes (5MB)
MAX_FILE_SIZE = 5 * 1024 * 1024

# Allowed image types
ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']


class CloudinaryService:
    """Service for handling image uploads to Cloudinary"""
    
    def __init__(self):
        self.configured = False
        self._configure()
    
    def _configure(self):
        """Configure Cloudinary with environment variables"""
        cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME')
        api_key = os.getenv('CLOUDINARY_API_KEY')
        api_secret = os.getenv('CLOUDINARY_API_SECRET')
        
        if all([cloud_name, api_key, api_secret]):
            cloudinary.config(
                cloud_name=cloud_name,
                api_key=api_key,
                api_secret=api_secret,
                secure=True
            )
            self.configured = True
            logger.info("✅ Cloudinary configured successfully")
        else:
            logger.warning("⚠️ Cloudinary not configured - missing environment variables")
            logger.warning("Required: CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET")
    
    def validate_file(self, file_data: bytes, filename: str, content_type: str) -> Dict[str, Any]:
        """
        Validate file before upload
        
        Args:
            file_data: File bytes
            filename: Original filename
            content_type: MIME type of the file
            
        Returns:
            Dict with 'valid' boolean and optional 'error' message
        """
        # Check file size
        if len(file_data) > MAX_FILE_SIZE:
            return {
                'valid': False,
                'error': f'File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB'
            }
        
        # Check content type
        if content_type not in ALLOWED_TYPES:
            return {
                'valid': False,
                'error': f'Invalid file type. Allowed types: {", ".join(ALLOWED_TYPES)}'
            }
        
        # Check extension
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return {
                'valid': False,
                'error': f'Invalid file extension. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
            }
        
        return {'valid': True}
    
    def upload_image(
        self,
        file_data: bytes,
        filename: str,
        content_type: str,
        ticket_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload image to Cloudinary
        
        Args:
            file_data: File bytes
            filename: Original filename
            content_type: MIME type
            ticket_id: Optional ticket ID for folder organization
            user_id: Optional user ID for tagging
            
        Returns:
            Dict with upload result including 'url' or 'error'
        """
        if not self.configured:
            return {
                'success': False,
                'error': 'Cloudinary not configured'
            }
        
        # Validate file
        validation = self.validate_file(file_data, filename, content_type)
        if not validation['valid']:
            return {
                'success': False,
                'error': validation['error']
            }
        
        try:
            # Build folder path
            folder = "ticket_system"
            if ticket_id:
                folder = f"ticket_system/tickets/{ticket_id}"
            elif user_id:
                folder = f"ticket_system/users/{user_id}"
            
            # Generate public_id from filename
            base_name = os.path.splitext(filename)[0]
            
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                file_data,
                folder=folder,
                public_id=base_name,
                resource_type="image",
                tags=[f"user_{user_id}"] if user_id else [],
                transformation=[
                    {'quality': 'auto:good'},
                    {'fetch_format': 'auto'}
                ]
            )
            
            logger.info(f"✅ Image uploaded successfully: {result['secure_url']}")
            
            return {
                'success': True,
                'url': result['secure_url'],
                'public_id': result['public_id'],
                'format': result['format'],
                'width': result.get('width'),
                'height': result.get('height'),
                'bytes': result.get('bytes')
            }
            
        except Exception as e:
            logger.error(f"❌ Cloudinary upload error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def upload_base64_image(
        self,
        base64_data: str,
        filename: str,
        ticket_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload base64 encoded image to Cloudinary
        
        Args:
            base64_data: Base64 encoded image string (with or without data URI prefix)
            filename: Original filename
            ticket_id: Optional ticket ID for folder organization
            user_id: Optional user ID for tagging
            
        Returns:
            Dict with upload result including 'url' or 'error'
        """
        if not self.configured:
            return {
                'success': False,
                'error': 'Cloudinary not configured'
            }
        
        try:
            # Handle data URI format
            if ',' in base64_data:
                header, base64_data = base64_data.split(',', 1)
                # Extract content type from header
                if 'image/jpeg' in header:
                    content_type = 'image/jpeg'
                elif 'image/png' in header:
                    content_type = 'image/png'
                elif 'image/gif' in header:
                    content_type = 'image/gif'
                elif 'image/webp' in header:
                    content_type = 'image/webp'
                else:
                    content_type = 'image/jpeg'  # Default
            else:
                # Guess from filename
                ext = os.path.splitext(filename)[1].lower()
                content_type_map = {
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png',
                    '.gif': 'image/gif',
                    '.webp': 'image/webp'
                }
                content_type = content_type_map.get(ext, 'image/jpeg')
            
            # Decode base64
            file_data = base64.b64decode(base64_data)
            
            return self.upload_image(
                file_data=file_data,
                filename=filename,
                content_type=content_type,
                ticket_id=ticket_id,
                user_id=user_id
            )
            
        except Exception as e:
            logger.error(f"❌ Base64 decode/upload error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_image(self, public_id: str) -> Dict[str, Any]:
        """
        Delete image from Cloudinary
        
        Args:
            public_id: Cloudinary public ID of the image
            
        Returns:
            Dict with deletion result
        """
        if not self.configured:
            return {
                'success': False,
                'error': 'Cloudinary not configured'
            }
        
        try:
            result = cloudinary.uploader.destroy(public_id)
            
            if result.get('result') == 'ok':
                logger.info(f"✅ Image deleted: {public_id}")
                return {'success': True}
            else:
                return {
                    'success': False,
                    'error': f"Deletion failed: {result.get('result')}"
                }
                
        except Exception as e:
            logger.error(f"❌ Cloudinary delete error: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Global singleton
cloudinary_service = CloudinaryService()
