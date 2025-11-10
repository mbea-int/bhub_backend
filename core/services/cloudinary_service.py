import cloudinary.uploader
import base64
import io
from PIL import Image
from django.conf import settings
import logging
import uuid

logger = logging.getLogger(__name__)


class CloudinaryService:
    """Service for handling Cloudinary uploads"""

    @staticmethod
    def upload_image(image_data, folder='general', resource_type='image'):
        """
        Upload image to Cloudinary

        Args:
            image_data: Can be file object, base64 string, or path
            folder: Cloudinary folder name
            resource_type: Type of resource (image, video, etc)

        Returns:
            dict: Cloudinary response or None if failed
        """
        try:
            upload_params = {
                'folder': f'muslim-community/{folder}',
                'resource_type': resource_type,
                'use_filename': True,
                'unique_filename': True,
                'overwrite': False,
                'transformation': settings.CLOUDINARY_DEFAULT_TRANSFORMATIONS
            }

            # Handle different types of image data
            if isinstance(image_data, str):
                if image_data.startswith('data:image'):
                    # Handle base64
                    result = cloudinary.uploader.upload(
                        image_data,
                        **upload_params
                    )
                else:
                    # Handle file path or URL
                    result = cloudinary.uploader.upload(
                        image_data,
                        **upload_params
                    )
            else:
                # Handle file object
                result = cloudinary.uploader.upload(
                    image_data,
                    **upload_params
                )

            return result

        except Exception as e:
            logger.error(f"Cloudinary upload error: {str(e)}")
            return None

    @staticmethod
    def upload_business_logo(image_data, business_name):
        """Upload business logo to Cloudinary"""
        public_id = f"business_logos/{uuid.uuid4()}"
        return CloudinaryService.upload_image(
            image_data,
            folder='businesses/logos',
            resource_type='image'
        )

    @staticmethod
    def upload_halal_certificate(image_data, business_name):
        """Upload halal certificate to Cloudinary"""
        public_id = f"halal_certificates/{uuid.uuid4()}"
        return CloudinaryService.upload_image(
            image_data,
            folder='businesses/certificates',
            resource_type='image'
        )

    @staticmethod
    def upload_user_profile_image(image_data, user_email):
        """Upload user profile image to Cloudinary"""
        public_id = f"profile_{user_email.split('@')[0]}_{uuid.uuid4()}"
        return CloudinaryService.upload_image(
            image_data,
            folder='users/profiles',
            resource_type='image'
        )

    @staticmethod
    def upload_post_image(image_data, post_id):
        """Upload post image to Cloudinary"""
        public_id = f"post_{post_id}"
        return CloudinaryService.upload_image(
            image_data,
            folder='posts',
            resource_type='image'
        )

    @staticmethod
    def delete_image(public_id):
        """Delete image from Cloudinary"""
        try:
            result = cloudinary.uploader.destroy(public_id)
            return result.get('result') == 'ok'
        except Exception as e:
            logger.error(f"Cloudinary delete error: {str(e)}")
            return False

    @staticmethod
    def get_optimized_url(url, width=None, height=None, crop='fill'):
        """Get optimized URL with transformations"""
        if not url or 'cloudinary' not in url:
            return url

        transformations = []
        if width:
            transformations.append(f'w_{width}')
        if height:
            transformations.append(f'h_{height}')
        if crop:
            transformations.append(f'c_{crop}')
        transformations.extend(['q_auto:eco', 'f_auto'])

        transform_str = ','.join(transformations)

        # Insert transformation into URL
        parts = url.split('/upload/')
        if len(parts) == 2:
            return f"{parts[0]}/upload/{transform_str}/{parts[1]}"
        return url