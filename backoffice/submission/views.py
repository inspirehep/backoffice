from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
import requests
from .serializers import AuthorSubmissionSerializer

class SubmissionViewSet(viewsets.ViewSet):
    
    @action(detail=False, methods=['post'])
    def author(self, request):


        serializer = AuthorSubmissionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # authentication?

        headers_django = {
    "Content-Type": "application/json",
    "Authorization": "Token 8b73f491a7da43e428ca88ca796c13d07f6fbd6d"
}
        
        headers_airflow = {
    "Content-Type": "application/json",
    "Authorization": "Basic YWlyZmxvdzphaXJmbG93"
}

        data =   {
            "workflow_type": "AUTHOR_CREATE",
            "data": {
            "$schema": "http://inspirebeta.net/schemas/records/authors.json",
            "name":{"value":"Macademia Nut"},
            "_collections":["Authors"]
            },
            "status": "running",
            "core": True,
            "is_update": True,
            "url":"https://rcs.com"
            }

        data["data"]["name"]["value"] = serializer.validated_data['name']

        request_url = 'http://localhost:8000/api/workflows/'
        response = requests.post(request_url, json=data, headers=headers_django)
        if response.status_code != 201:
            return Response({  'message': 'request to django api failed',
                                'request': {'url':response,'data':data},
                                'response':{
                                            'code':response.status_code,
                                            'data':response.json()}
                                            },
                                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        data = {
        "conf":
            {
                "workflow_id": response.json()['id']
            }
        }

        request_url = 'http://airflow-webserver:8080/api/v1/dags/author_create_initialization_dag/dagRuns'
        response = requests.post(request_url, json=data, headers=headers_airflow)

        if response.status_code != 200:
            return Response({  'message': 'request to airflow failed',
                                'request': {'url':response,'data':data},
                                'response':{
                                            'code':response.status_code,
                                            'data':response.json()}
                                            },
                                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        return Response({'message': 'workflow triggered successfully',
                         'airflow_status_code':response.status_code,
                         'data':data}, status=status.HTTP_200_OK)
    

