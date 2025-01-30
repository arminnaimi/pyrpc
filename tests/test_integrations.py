"""Tests for PyRPC framework integrations"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from flask import Flask
from django.urls import path, include, re_path
from django.test import Client as DjangoClient
from django.test import RequestFactory
import json
from pyrpc import PyRPCFastAPI, PyRPCFlask, PyRPCDjango
from tests.conftest import HelloInput, HelloOutput

@pytest.fixture
def fastapi_app(router):
    """Create a FastAPI test application"""
    app = FastAPI()
    trpc = PyRPCFastAPI(router)
    trpc.mount(app)
    return app

@pytest.fixture
def flask_app(router):
    """Create a Flask test application"""
    app = Flask(__name__)
    trpc = PyRPCFlask(router)
    trpc.mount(app)
    return app

@pytest.fixture
def django_urlpatterns(router):
    """Create Django URL patterns"""
    urlpatterns = []
    trpc = PyRPCDjango(router)
    trpc.mount(urlpatterns)
    return urlpatterns

def test_fastapi_integration(fastapi_app):
    """Test FastAPI integration"""
    client = TestClient(fastapi_app)
    
    # Test query
    response = client.post(
        "/trpc/query/hello",
        json={"input": {"name": "World"}}
    )
    assert response.status_code == 200
    assert response.json() == {
        "result": {"message": "Hello World!"},
        "success": True
    }
    
    # Test health check
    response = client.get("/trpc/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_flask_integration(flask_app):
    """Test Flask integration"""
    client = flask_app.test_client()
    
    # Test query
    response = client.post(
        "/trpc/query/hello",
        json={"input": {"name": "World"}}
    )
    assert response.status_code == 200
    assert response.get_json() == {
        "result": {"message": "Hello World!"},
        "success": True
    }
    
    # Test health check
    response = client.get("/trpc/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "healthy"}

def test_django_integration(django_urlpatterns):
    """Test Django integration"""
    # Create test URLs
    root_urlpatterns = [
        path("", include(django_urlpatterns)),
    ]
    
    # Create test client
    factory = RequestFactory()
    
    # Test query
    request = factory.post(
        "/trpc/query/hello",
        data=json.dumps({"input": {"name": "World"}}),
        content_type="application/json"
    )
    
    # Find the view function
    for pattern in django_urlpatterns:
        if pattern.pattern.match("/trpc/query/hello"):
            view = pattern.callback.view_class.as_view()
            response = view(request, path="hello")
            assert response.status_code == 200
            response_data = json.loads(response.content)
            assert response_data == {
                "result": {"message": "Hello World!"},
                "success": True
            }
            break
    
    # Test health check
    request = factory.get("/trpc/health")
    for pattern in django_urlpatterns:
        if pattern.pattern.match("/trpc/health"):
            view = pattern.callback.view_class.as_view()
            response = view(request)
            assert response.status_code == 200
            assert json.loads(response.content) == {"status": "healthy"}
            break

def test_integration_error_handling(fastapi_app):
    """Test error handling in integrations"""
    client = TestClient(fastapi_app)
    
    # Test invalid input
    response = client.post(
        "/trpc/query/hello",
        json={"input": {"wrong_field": "value"}}
    )
    assert response.status_code == 200
    assert response.json()["success"] is False
    assert "error" in response.json()
    
    # Test not found
    response = client.post(
        "/trpc/query/non_existent",
        json={"input": {}}
    )
    assert response.status_code == 200
    assert response.json()["success"] is False
    assert response.json()["error"]["code"] == "NOT_FOUND" 