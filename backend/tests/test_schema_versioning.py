import pytest
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_schema_generation():
    client = APIClient()
    url = reverse("schema")
    response = client.get(url)
    assert response.status_code == 200
    assert "openapi" in response.data


@pytest.mark.django_db
def test_swagger_ui():
    client = APIClient()
    url = reverse("swagger-ui")
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_redoc():
    client = APIClient()
    url = reverse("redoc")
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_api_versioning_v1_v2():
    client = APIClient()
    # v1 summary endpoint existence check (401 expected due to auth)
    v1_url = "/api/v1/summary/"
    v1_response = client.get(v1_url)
    assert v1_response.status_code == 401

    # v2 summary endpoint existence check (401 expected due to auth)
    v2_url = "/api/v2/summary/"
    v2_response = client.get(v2_url)
    assert v2_response.status_code == 401
