
from django.urls import path, include
from . import  views


from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('categories', views.ClassCategoryViewSet, basename='category')
router.register('courses', views.CourseViewSet, basename='course')
router.register('lessons', views.LessonViewSet, basename='lesson')

router.register('users', views.UserViewSet, basename='user')

router.register('comments', views.CommentViewSet, basename='comment')

router.register('apointment', views.ApointmentViewSet, basename='apointment')

from .views import VNPayCreateUrl, VNPayReturnView

# router.register('chat', views.ChatViewSet, basename='chat')
urlpatterns = [
    path('', include(router.urls)),
    path('order/create_payment_url/', VNPayCreateUrl.as_view(), name='vnpay-create'),
    path('payment/vnpay-return/', VNPayReturnView.as_view(), name='vnpay-return'),
]
