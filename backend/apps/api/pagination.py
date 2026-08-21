from django.conf import settings
from rest_framework.pagination import PageNumberPagination
from rest_framework.settings import api_settings


class StandardResultsSetPagination(PageNumberPagination):
    """Bounded, client-tunable pagination shared by collection endpoints."""

    page_size = api_settings.PAGE_SIZE
    page_size_query_param = "page_size"
    max_page_size = settings.API_MAX_PAGE_SIZE
