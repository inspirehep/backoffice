import logging

from django.shortcuts import get_object_or_404
from django_elasticsearch_dsl_drf.filter_backends import (
    CompoundSearchFilterBackend,
    DefaultOrderingFilterBackend,
    FacetedSearchFilterBackend,
    FilteringFilterBackend,
    OrderingFilterBackend,
)
from django_elasticsearch_dsl_drf.viewsets import BaseDocumentViewSet
from opensearch_dsl import TermsFacet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from backoffice.utils.pagination import OSStandardResultsSetPagination
from backoffice.workflows import airflow_utils
from backoffice.workflows.api.serializers import (
    AuthorResolutionSerializer,
    WorkflowDocumentSerializer,
    WorkflowSerializer,
    WorkflowTicketSerializer,
)
from backoffice.workflows.constants import WORKFLOW_DAGS, ResolutionDags
from backoffice.workflows.documents import WorkflowDocument
from backoffice.workflows.models import Workflow, WorkflowTicket

logger = logging.getLogger(__name__)


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
        serializer = WorkflowSerializer(
            workflow_instance, data=request.data, partial=True
        )

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
                {"error": "Both workflow_id and ticket_type are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            workflow_ticket = WorkflowTicket.objects.get(
                workflow_id=workflow_id, ticket_type=ticket_type
            )
            serializer = WorkflowTicketSerializer(workflow_ticket)
            return Response(serializer.data)
        except WorkflowTicket.DoesNotExist:
            return Response(
                {"error": "Workflow ticket not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

    def create(self, request, *args, **kwargs):
        workflow_id = request.data.get("workflow_id")
        ticket_type = request.data.get("ticket_type")
        ticket_id = request.data.get("ticket_id")

        if not all([workflow_id, ticket_type, ticket_id]):
            return Response(
                {"error": "Workflow_id, ticket_id and ticket_type are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            workflow = Workflow.objects.get(id=workflow_id)
            workflow_ticket = WorkflowTicket.objects.create(
                workflow_id=workflow, ticket_id=ticket_id, ticket_type=ticket_type
            )
            serializer = WorkflowTicketSerializer(workflow_ticket)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AuthorWorkflowViewSet(viewsets.ViewSet):
    serializer_class = WorkflowSerializer

    def create(self, request):
        logger.info("Creating workflow with data: %s", request.data)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            workflow = Workflow.objects.create(
                data=serializer.validated_data["data"],
                workflow_type=serializer.validated_data["workflow_type"],
            )
        logger.info(
            "Trigger Airflow DAG: %s for %s",
            WORKFLOW_DAGS[workflow.workflow_type].initialize,
            workflow.id,
        )
        return airflow_utils.trigger_airflow_dag(
            WORKFLOW_DAGS[workflow.workflow_type].initialize,
            str(workflow.id),
            workflow.data,
        )

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        logger.info("Resolving data: %s", request.data)
        serializer = AuthorResolutionSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            extra_data = {"create_ticket": serializer.validated_data["create_ticket"]}
            logger.info(
                "Trigger Airflow DAG: %s for %s",
                ResolutionDags[serializer.validated_data["value"]],
                pk,
            )

            return airflow_utils.trigger_airflow_dag(
                ResolutionDags[serializer.validated_data["value"]].label, pk, extra_data
            )

    @action(detail=True, methods=["post"])
    def restart(self, request, pk=None):
        workflow = Workflow.objects.get(id=pk)

        if request.data.get("restart_current_task"):
            return airflow_utils.restart_failed_tasks(workflow)

        return airflow_utils.restart_workflow_dags(
            workflow.id, workflow.workflow_type, request.data.get("params")
        )


class WorkflowDocumentView(BaseDocumentViewSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.search = self.search.extra(track_total_hits=True)

    document = WorkflowDocument
    serializer_class = WorkflowSerializer
    pagination_class = OSStandardResultsSetPagination
    filter_backends = [
        DefaultOrderingFilterBackend,
        CompoundSearchFilterBackend,
        FacetedSearchFilterBackend,
        FilteringFilterBackend,
        OrderingFilterBackend,
    ]
    search_fields = {
        "workflow_type",
        "status",
        "is_update",
    }

    filter_fields = {"status": "status", "workflow_type": "workflow_type"}

    ordering_fields = {"_updated_at": "_updated_at"}

    ordering = ("-_updated_at",)

    faceted_search_fields = {
        "status": {
            "field": "status.keyword",
            "facet": TermsFacet,
            "options": {
                "size": 10,
                "order": {
                    "_key": "asc",
                },
            },
            "enabled": True,
        },
        "workflow_type": {
            "field": "workflow_type.keyword",
            "facet": TermsFacet,
            "options": {
                "size": 10,
                "order": {
                    "_key": "asc",
                },
            },
            "enabled": True,
        },
    }

    def get_serializer_class(self):
        return WorkflowDocumentSerializer
