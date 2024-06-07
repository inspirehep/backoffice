from django.urls import include, path
from rest_framework.routers import DefaultRouter
from backoffice.workflows.api.views import WorflowSubmissionViewSet

app_name = 'workflow-submissions'

router = DefaultRouter()
router.register(r"workflow", WorflowSubmissionViewSet, basename="workflow-submissionsss")

urlpatterns = [
    path("", include(router.urls), name= "workflow-submissions"),
]