from django_elasticsearch_dsl_drf.filter_backends import (
    MultiMatchSearchFilterBackend,
)


class CustomMultiMatchSearchFilterBackend(MultiMatchSearchFilterBackend):
    search_param = "search"
