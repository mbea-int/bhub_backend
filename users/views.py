from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from .models import User, BlockedUser
from .serializers import (
    UserRegistrationSerializer, UserProfileSerializer,
    UserUpdateSerializer, BlockedUserSerializer
)
from core.services.cloudinary_service import CloudinaryService
import logging

logger = logging.getLogger(__name__)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegistrationSerializer
        elif self.action in ['update', 'partial_update', 'update_profile']:
            return UserUpdateSerializer
        return UserProfileSerializer

    def get_permissions(self):
        public_actions = ['create', 'guest_login']

        if self.action in public_actions:
            return [permissions.AllowAny()]

        return [permissions.IsAuthenticated()]

    @method_decorator(ratelimit(key='ip', rate='5/15m', method='POST'))
    def create(self, request, *args, **kwargs):
        """Register new user"""
        data = request.data.copy()

        # Handle profile image if provided during registration
        if 'profile_image' in data and data['profile_image']:
            if not data['profile_image'].startswith('http'):
                # Upload to Cloudinary
                image_result = CloudinaryService.upload_user_profile_image(
                    data['profile_image'],
                    data.get('email', 'user')
                )
                if image_result:
                    data['profile_image'] = image_result['secure_url']
                    logger.info(f"Profile image uploaded during registration: {image_result['secure_url']}")
                else:
                    logger.error("Failed to upload profile image during registration")
                    data.pop('profile_image', None)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """Update current user profile"""
        user = request.user
        data = request.data.copy()

        # Handle profile image upload
        if 'profile_image' in data and data['profile_image']:
            # Check if it's a new image (not already a URL)
            if not data['profile_image'].startswith('http'):
                try:
                    # Delete old image if exists and is from Cloudinary
                    if user.profile_image and 'cloudinary' in user.profile_image:
                        old_public_id = self._extract_public_id(user.profile_image)
                        if old_public_id:
                            CloudinaryService.delete_image(old_public_id)
                            logger.info(f"Deleted old profile image: {old_public_id}")

                    # Upload new image
                    image_result = CloudinaryService.upload_user_profile_image(
                        data['profile_image'],
                        user.email
                    )

                    if image_result:
                        data['profile_image'] = image_result['secure_url']
                        logger.info(f"Profile image uploaded: {image_result['secure_url']}")
                    else:
                        logger.error("Failed to upload profile image")
                        return Response(
                            {'error': 'Failed to upload profile image'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                except Exception as e:
                    logger.error(f"Error handling profile image upload: {str(e)}")
                    return Response(
                        {'error': 'Error processing image upload'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

        serializer = UserUpdateSerializer(user, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(UserProfileSerializer(user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['delete'])
    def delete_profile_image(self, request):
        """Delete user's profile image"""
        user = request.user

        if user.profile_image:
            try:
                # Delete from Cloudinary if it's a Cloudinary URL
                if 'cloudinary' in user.profile_image:
                    public_id = self._extract_public_id(user.profile_image)
                    if public_id:
                        CloudinaryService.delete_image(public_id)
                        logger.info(f"Deleted profile image: {public_id}")

                # Clear the profile image field
                user.profile_image = None
                user.save()

                return Response({'detail': 'Profile image deleted successfully'})
            except Exception as e:
                logger.error(f"Error deleting profile image: {str(e)}")
                return Response(
                    {'error': 'Failed to delete profile image'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response({'detail': 'No profile image to delete'})

    @action(detail=False, methods=['post'])
    def upload_profile_image(self, request):
        """Upload only profile image"""
        if 'profile_image' not in request.data:
            return Response(
                {'error': 'No image provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Use the update_profile method with only image data
        return self.update_profile(request)

    # @action(detail=False, methods=['post'])
    # def upgrade_to_business(self, request):
    #     """Upgrade regular user to business owner"""
    #     user = request.user
    #     if user.user_type == 'business':
    #         return Response(
    #             {'detail': 'Already a business owner'},
    #             status=status.HTTP_400_BAD_REQUEST
    #         )
    #
    #     user.user_type = 'business'
    #     user.save()
    #     return Response({'detail': 'Successfully upgraded to business owner'})

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def upgrade_to_business(self, request):
        """Upgrade user to business owner"""
        user = request.user

        # Validations
        if user.user_type == 'business':
            return Response(
                {'detail': 'Already a business owner'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if user.user_type == 'guest':
            return Response(
                {'detail': 'Guest users cannot become business owners'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Upgrade user
        user.user_type = 'business'
        user.save()

        # Return updated user data
        user_serializer = UserProfileSerializer(user)

        logger.info(f"User {user.email} upgraded to business owner")

        return Response({
            'detail': 'Successfully upgraded to business owner',
            'user': user_serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def downgrade_to_regular(self, request):
        """Downgrade from business owner to regular user"""
        user = request.user

        if user.user_type != 'business':
            return Response(
                {'detail': 'User is not a business owner'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user has active businesses
        active_businesses = user.businesses.count()
        if active_businesses > 0:
            return Response(
                {
                    'detail': 'Cannot downgrade while you have active businesses',
                    'active_businesses': active_businesses,
                    'message': 'Please delete all businesses before downgrading'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Downgrade user
        user.user_type = 'regular'
        user.save()

        # Return updated user data
        user_serializer = UserProfileSerializer(user)

        logger.info(f"User {user.email} downgraded to regular user")

        return Response({
            'detail': 'Successfully downgraded to regular user',
            'user': user_serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def block(self, request, pk=None):
        """Block a user"""
        user_to_block = self.get_object()
        if user_to_block == request.user:
            return Response(
                {'detail': 'Cannot block yourself'},
                status=status.HTTP_400_BAD_REQUEST
            )

        blocked, created = BlockedUser.objects.get_or_create(
            blocker=request.user,
            blocked=user_to_block
        )

        if created:
            return Response({'detail': 'User blocked successfully'})
        return Response(
            {'detail': 'User already blocked'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['post'])
    def unblock(self, request, pk=None):
        """Unblock a user"""
        user_to_unblock = self.get_object()
        deleted = BlockedUser.objects.filter(
            blocker=request.user,
            blocked=user_to_unblock
        ).delete()

        if deleted[0] > 0:
            return Response({'detail': 'User unblocked successfully'})
        return Response(
            {'detail': 'User was not blocked'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['get'])
    def blocked_users(self, request):
        """Get list of blocked users"""
        blocked = BlockedUser.objects.filter(blocker=request.user)
        serializer = BlockedUserSerializer(blocked, many=True)
        return Response(serializer.data)

    def _extract_public_id(self, cloudinary_url):
        """Extract public_id from Cloudinary URL"""
        try:
            # Example URL: https://res.cloudinary.com/demo/image/upload/v1234/folder/public_id.jpg
            parts = cloudinary_url.split('/')
            # Find the upload index
            upload_index = parts.index('upload')
            # Get everything after version (v1234)
            public_id_with_ext = '/'.join(parts[upload_index + 2:])
            # Remove file extension
            public_id = public_id_with_ext.rsplit('.', 1)[0]
            return public_id
        except Exception as e:
            logger.error(f"Error extracting public_id from URL: {str(e)}")
            return None

    @action(detail=False, methods=['get'])
    def get_profile_image_upload_url(self, request):
        """Get optimized profile image URL for different sizes"""
        user = request.user
        if not user.profile_image:
            return Response({'profile_image': None})

        return Response({
            'original': user.profile_image,
            'thumbnail': CloudinaryService.get_optimized_url(
                user.profile_image,
                width=150,
                height=150,
                crop='fill'
            ),
            'medium': CloudinaryService.get_optimized_url(
                user.profile_image,
                width=400,
                height=400,
                crop='fill'
            ),
            'large': CloudinaryService.get_optimized_url(
                user.profile_image,
                width=800,
                height=800,
                crop='fill'
            )
        })

    @action(detail=False, methods=['post'], url_path='guest-login', permission_classes=[permissions.AllowAny])
    def guest_login(self, request):
        """Create guest access"""
        from datetime import timedelta
        from django.utils import timezone
        import secrets

        try:
            # Check if create_guest_user exists in UserManager
            if hasattr(User.objects, 'create_guest_user'):
                guest_user = User.objects.create_guest_user()
            else:
                # Fallback - create manually
                guest_email = f"guest_{secrets.token_hex(8)}@temp.local"
                guest_user = User(
                    email=guest_email,
                    full_name="Vizitor",
                    user_type='regular',  # ose 'guest' nëse e ke
                    is_active=True,
                )
                # Set guest flag if field exists
                if hasattr(guest_user, 'is_guest'):
                    guest_user.is_guest = True

                guest_user.set_unusable_password()
                guest_user.save()

            # Set expiration if field exists
            if hasattr(guest_user, 'guest_expires_at'):
                guest_user.guest_expires_at = timezone.now() + timedelta(days=7)
                guest_user.save()

            # Generate token
            refresh = RefreshToken.for_user(guest_user)

            return Response({
                'user': UserProfileSerializer(guest_user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
                'is_guest': True,
                'expires_at': guest_user.guest_expires_at.isoformat() if hasattr(guest_user,
                                                                                 'guest_expires_at') else None
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Guest login error: {str(e)}")
            return Response(
                {'error': 'Failed to create guest session', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )