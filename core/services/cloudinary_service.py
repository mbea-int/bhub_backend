import cloudinary.uploader
from django.conf import settings
import logging
import uuid

logger = logging.getLogger(__name__)


class CloudinaryService:
    """Service for handling Cloudinary uploads"""

    @staticmethod
    def upload_image(image_data, folder='general', resource_type='image'):
        try:
            upload_params = {
                'folder': f'muslim-community/{folder}',
                'resource_type': resource_type,
                'use_filename': True,
                'unique_filename': True,
                'overwrite': False,
                'transformation': settings.CLOUDINARY_DEFAULT_TRANSFORMATIONS
            }

            result = cloudinary.uploader.upload(image_data, **upload_params)

            # ✅ Kthe edhe public_id edhe url
            return {
                'secure_url': result.get('secure_url'),
                'public_id': result.get('public_id'),
                'format': result.get('format'),
                'width': result.get('width'),
                'height': result.get('height'),
            }

        except Exception as e:
            logger.error(f"Cloudinary upload error: {str(e)}")
            return None

    @staticmethod
    def upload_business_logo(image_data, business_name):
        """Upload business logo to Cloudinary"""
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
        """Delete image from Cloudinary using public_id"""
        try:
            if not public_id:
                return False

            result = cloudinary.uploader.destroy(public_id, invalidate=True)
            logger.info(f"Cloudinary delete result: {result}")
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