from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SubmissionViewSet

router = DefaultRouter()
router.register(r'submission', SubmissionViewSet, basename='submission')

urlpatterns = [
    path('', include(router.urls)),
]