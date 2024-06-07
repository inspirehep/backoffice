from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.response import Response
<<<<<<< HEAD
from rest_framework.decorators import action
=======
from django_elasticsearch_dsl_drf.viewsets import BaseDocumentViewSet

>>>>>>> 71ed612 (search: minor fixes on elastic search implementation)
from backoffice.workflows.models import Workflow, WorkflowTicket
from backoffice.workflows.documents import WorkflowDocument
from backoffice.utils.pagination import OSStandardResultsSetPagination
from .serializers import WorkflowSerializer, WorkflowTicketSerializer, WorkflowDocumentSerializer

from backoffice.workflows import airflow_utils

class WorkflowViewSet(viewsets.ModelViewSet):
    queryset = Workflow.objects.all()
    serializer_class = WorkflowSerializer

    def get_queryset(self):
        status = self.request.query_params.get("status")
        if status:
            return self.queryset.filter(status__status=status)
        return self.queryset


class WorkflowPartialUpdateViewSet(viewsets.ViewSet):
    def partial_update(self, request, pk=None):
        workflow_instance = get_object_or_404(Workflow, pk=pk)
        serializer = WorkflowSerializer(workflow_instance, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WorkflowTicketViewSet(viewsets.ViewSet):
    def retrieve(self, request, *args, **kwargs):
        workflow_id = kwargs.get("pk")
        ticket_type = request.query_params.get("ticket_type")

        if not workflow_id or not ticket_type:
            return Response(
                {"error": "Both workflow_id and ticket_type are required."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            workflow_ticket = WorkflowTicket.objects.get(workflow_id=workflow_id, ticket_type=ticket_type)
            serializer = WorkflowTicketSerializer(workflow_ticket)
            return Response(serializer.data)
        except WorkflowTicket.DoesNotExist:
            return Response({"error": "Workflow ticket not found."}, status=status.HTTP_404_NOT_FOUND)

    def create(self, request, *args, **kwargs):
        workflow_id = request.data.get("workflow_id")
        ticket_type = request.data.get("ticket_type")
        ticket_id = request.data.get("ticket_id")

        if not all([workflow_id, ticket_type, ticket_id]):
            return Response(
                {"error": "Workflow_id, ticket_id and ticket_type are required."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            workflow = Workflow.objects.get(id=workflow_id)
            workflow_ticket = WorkflowTicket.objects.create(
                workflow_id=workflow, ticket_id=ticket_id, ticket_type=ticket_type
            )
            serializer = WorkflowTicketSerializer(workflow_ticket)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

<<<<<<< HEAD
class WorflowSubmissionViewSet(viewsets.ViewSet):

    @action(detail=False, methods=['post'])
    def submit(self, request):

        # TODO workflow submission serializer

        # create workflow entry
        workflow = Workflow.objects.create(
            data=request.data, 
            status="approval",
            core=True, is_update=False,workflow_type="AUTHOR_CREATE")

        print('Triggering dag')        
        # response id, corresponds to the new workflow id
        response = airflow_utils.trigger_airflow_dag('author_create_initialization_dag',str(workflow.id))

        return Response({'data':response.content,
                         'status_code':response.status_code}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def resolve(self, request):

        data = request.data
        create_ticket = data['create_ticket']
        resolution = data['resolution']
        extra_data = {'create_ticket':create_ticket, 'resolution': resolution}

        if resolution == 'accept':
            dag_name = 'author_create_approved_dag'
        elif resolution == 'reject':
            dag_name = 'author_create_rejected_dag'
        else:
            return Response(
                {'message':'resolution method unrecognized'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        response = airflow_utils.trigger_airflow_dag(dag_name, data['id'], extra_data)

        return Response({'data':response.content,
                         'status_code':response.status_code}, status=status.HTTP_200_OK)
=======

class WorkflowDocumentView(BaseDocumentViewSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.search = self.search.extra(track_total_hits=True)

    document = WorkflowDocument
    serializer_class = WorkflowSerializer
    pagination_class = OSStandardResultsSetPagination

    search_fields = {
        "workflow_type",
        "status",
        "is_update",
    }
    ordering = ["_updated_at"]

    def get_serializer_class(self):
        return WorkflowDocumentSerializer
>>>>>>> 71ed612 (search: minor fixes on elastic search implementation)
