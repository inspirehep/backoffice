from django.shortcuts import get_object_or_404
from django_elasticsearch_dsl_drf.viewsets import BaseDocumentViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from backoffice.utils.pagination import OSStandardResultsSetPagination
from backoffice.workflows import airflow_utils
from backoffice.workflows.documents import WorkflowDocument
from backoffice.workflows.models import Workflow, WorkflowTicket

from ..constants import WORKFLOW_TYPES
from .serializers import WorkflowDocumentSerializer, WorkflowSerializer, WorkflowTicketSerializer


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


class AuthorWorkflowViewSet(viewsets.ViewSet):
    def create(self, request):

        workflow = Workflow.objects.create(data=request.data["data"], workflow_type=request.data["workflow_type"])
        serializer = WorkflowSerializer(workflow)

        if workflow.workflow_type == WORKFLOW_TYPES[2][0]:
            dag_name = "author_create_initialization_dag"
        elif workflow.workflow_type == WORKFLOW_TYPES[3][0]:
            dag_name = "author_update_dag"
        else:
            return Response({"message": "workflow_type unrecognized"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return airflow_utils.trigger_airflow_dag(dag_name, str(workflow.id), serializer.data)

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):

        data = request.data
        create_ticket = data["create_ticket"]
        resolution = data["value"]
        extra_data = {"create_ticket": create_ticket, "resolution": resolution}

        if resolution == "accept":
            dag_name = "author_create_approved_dag"
        elif resolution == "reject":
            dag_name = "author_create_rejected_dag"
        else:
            return Response(
                {"message": "resolution method unrecognized"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        response = airflow_utils.trigger_airflow_dag(dag_name, pk, extra_data)

        return Response({"data": response.content, "status_code": response.status_code}, status=status.HTTP_200_OK)


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
