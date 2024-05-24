from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
import requests

from . import airflow_utils

from .serializers import AuthorSubmissionSerializer

from django.apps import apps
Workflow = apps.get_model(app_label="workflows", model_name="Workflow")
# from workflows.models import Workflow

class SubmissionViewSet(viewsets.ViewSet):

    @action(detail=False, methods=['post'])
    def author(self, request):

        # TODO: should this serialization be properly implemented here, later or in multiple places
        serializer = AuthorSubmissionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # create workflow entry
        workflow = Workflow.objects.create(
            data=serializer.validated_data, 
            status="approval",
            core=True, is_update=False, url="https://www.unusedfield.com",workflow_type="AUTHOR_CREATE")

        print('Triggering dag')        
        # response id, corresponds to the new workflow id
        response = airflow_utils.trigger_airflow_dag('author_create_initialization_dag',str(workflow.id))

        return Response({'message': 'workflow triggered successfully',
                         'data':response.content,
                         'status_code':response.status_code}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def authorapproval(self, request):

        data = request.data

        extra_data = {'create_ticket':True}
        response = airflow_utils.trigger_airflow_dag('author_create_approved_dag',data['id'],extra_data)

        return Response({'message': 'workflow triggered successfully',
                         'data':response.content,
                         'status_code':response.status_code}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def authorrejection(self, request):

        data = request.data

        response = airflow_utils.trigger_airflow_dag('author_create_rejected_dag',data['id'])

        return Response({'message': 'workflow triggered successfully',
                         'data':response.content,
                         'status_code':response.status_code}, status=status.HTTP_200_OK)
