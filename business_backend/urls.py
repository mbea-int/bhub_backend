from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# Import all viewsets
from users.views import UserViewSet
from businesses.views import BusinessViewSet, BusinessCategoryViewSet
from posts.views import PostViewSet, ProductCategoryViewSet
from reviews.views import InquiryViewSet, ReviewViewSet
from groups.views import GroupViewSet, GroupPostViewSet
from notifications.views import NotificationViewSet
from messaging.views import MessageViewSet
from reports.views import ReportViewSet

# Create router
router = DefaultRouter()

# Register all endpoints
router.register(r'users', UserViewSet, basename='user')
router.register(r'businesses', BusinessViewSet, basename='business')
router.register(r'business-categories', BusinessCategoryViewSet, basename='business-category')
router.register(r'posts', PostViewSet, basename='post')
router.register(r'product-categories', ProductCategoryViewSet, basename='product-category')
router.register(r'inquiries', InquiryViewSet, basename='inquiry')
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'groups', GroupViewSet, basename='group')
router.register(r'group-posts', GroupPostViewSet, basename='grouppost')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'reports', ReportViewSet, basename='report')

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # JWT Authentication
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # API Routes
    path('api/', include(router.urls)),

    # Browsable API login
    path('api-auth/', include('rest_framework.urls')),
]

# Servo media files në development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom admin site configuration
admin.site.site_header = "NYJA Admin"
admin.site.site_title = "NYJA Admin Portal"
admin.site.index_title = "Welcome to NYJA Administration"