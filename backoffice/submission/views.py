from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
import requests

from . import airflow_utils

from .serializers import AuthorSubmissionSerializer

class SubmissionViewSet(viewsets.ViewSet):

    @action(detail=False, methods=['post'])
    def author(self, request):

        # TODO: should this serialization be properly implemented here, later or in multiple places
        serializer = AuthorSubmissionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # authentication?

        headers_django = {
    "Content-Type": "application/json",
    "Authorization": "Token 8b73f491a7da43e428ca88ca796c13d07f6fbd6d"
}

        # # this data does not need to be this complete yet
        data =   {
            "workflow_type": "AUTHOR_CREATE",
            "data": None,
            "status": "running",
            "core": False,
            "is_update": False,
            "url":"https://www.unusedfield.com"
            }

        data['data'] = serializer.validated_data

        request_url = 'http://localhost:8000/api/workflows/'
        response = requests.post(request_url, json=data, headers=headers_django, timeout=10)
        if response.status_code != 201:
            return Response({  'message': 'request to django api failed',
                                'request': {'url':response,'data':data},
                                'response':{
                                            'code':response.status_code,
                                            'data':response.json()}
                                            },
                                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        print('Triggering dag')

        
        # response id, corresponds to the new workflow id
        response = airflow_utils.trigger_airflow_dag('author_create_initialization_dag',response.json()['id'])

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
