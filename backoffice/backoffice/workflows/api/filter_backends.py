from django_elasticsearch_dsl_drf.filter_backends import (
    SimpleQueryStringSearchFilterBackend,
)


class CustomSimpleQueryStringSearchFilterBackend(SimpleQueryStringSearchFilterBackend):
    search_param = "search"
