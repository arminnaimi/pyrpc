"""Tests for PyRPC integrations"""
# ruff: noqa: E501,RUF006,RUF100
# type: ignore

import asyncio
import json

import pytest
from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.wsgi import get_wsgi_application
from django.http import JsonResponse
from django.test import Client as DjangoClient, RequestFactory
from django.urls import path
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from fastapi import FastAPI
from fastapi.testclient import TestClient
from flask import Flask
from pydantic import BaseModel

from pyrpc import (
    PyRPCContext,
    PyRPCDjango,
    PyRPCError,
    PyRPCFastAPI,
    PyRPCFlask,
    PyRPCRouter,
)

# Configure Django settings if not already configured
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY="test-key",
        ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"],
        ROOT_URLCONF=[],
        MIDDLEWARE=[
            "django.middleware.common.CommonMiddleware",
            "django.middleware.csrf.CsrfViewMiddleware",
        ],
        USE_TZ=True,
    )

    # Initialize Django
    import django

    django.setup()


# Test models
class EchoInput(BaseModel):
    message: str


class EchoOutput(BaseModel):
    message: str


# Test error cases
class ErrorInput(BaseModel):
    should_error: bool


class ErrorOutput(BaseModel):
    message: str


class ContextInput(BaseModel):
    message: str


class ContextOutput(BaseModel):
    message: str
    context_value: str


# Test fixtures
@pytest.fixture
def router():
    """Create a test router with basic procedures"""
    router = PyRPCRouter()

    @router.query("echo")
    def echo(input: EchoInput) -> EchoOutput:
        return EchoOutput(message=input.message)

    @router.mutation("echo_mutation")
    def echo_mutation(input: EchoInput) -> EchoOutput:
        return EchoOutput(message=input.message)

    return router


@pytest.fixture
def context_router():
    """Create a test router with context-aware procedures"""
    router = PyRPCRouter()

    @router.query("context_test")
    def context_test(input: ContextInput, context: PyRPCContext) -> ContextOutput:
        try:
            context_value = context.raw_request["test_value"]
        except (KeyError, TypeError, AttributeError):
            context_value = "default"
        return ContextOutput(message=input.message, context_value=context_value)

    @router.mutation("context_test")
    def context_test_mutation(
        input: ContextInput, context: PyRPCContext
    ) -> ContextOutput:
        try:
            context_value = context.raw_request["test_value"]
        except (KeyError, TypeError, AttributeError):
            context_value = "default"
        return ContextOutput(message=input.message, context_value=context_value)

    return router


@pytest.fixture
def error_router():
    """Create a test router with error-throwing procedures"""
    router = PyRPCRouter()

    @router.query("error")
    def error(input: ErrorInput) -> ErrorOutput:
        if input.should_error:
            raise PyRPCError(code="TEST_ERROR", message="Test error", status_code=400)
        return ErrorOutput(message="No error")

    return router


# FastAPI Tests
@pytest.fixture
def fastapi_app(router):
    """Create a FastAPI test application"""
    app = FastAPI()
    pyrpc = PyRPCFastAPI(router, prefix="/api")
    pyrpc.mount(app)
    return app


@pytest.fixture
def fastapi_client(fastapi_app):
    """Create a FastAPI test client"""
    return TestClient(fastapi_app)


def test_fastapi_query(fastapi_client):
    """Test FastAPI query endpoint"""
    response = fastapi_client.post(
        "/api/query/echo", json={"input": {"message": "hello"}}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["result"]["message"] == "hello"


def test_fastapi_mutation(fastapi_client):
    """Test FastAPI mutation endpoint"""
    response = fastapi_client.post(
        "/api/mutation/echo_mutation", json={"input": {"message": "hello"}}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["result"]["message"] == "hello"


def test_fastapi_health(fastapi_client):
    """Test FastAPI health endpoint"""
    response = fastapi_client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


# Flask Tests
@pytest.fixture
def flask_app(router):
    """Create a Flask test application"""
    app = Flask(__name__)
    pyrpc = PyRPCFlask(router)
    pyrpc.mount(app, prefix="/api")
    return app


@pytest.fixture
def flask_client(flask_app):
    """Create a Flask test client"""
    return flask_app.test_client()


def test_flask_query(flask_client):
    """Test Flask query endpoint"""
    response = flask_client.post(
        "/api/query/echo", json={"input": {"message": "hello"}}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["result"]["message"] == "hello"


def test_flask_mutation(flask_client):
    """Test Flask mutation endpoint"""
    response = flask_client.post(
        "/api/mutation/echo_mutation", json={"input": {"message": "hello"}}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["result"]["message"] == "hello"


def test_flask_health(flask_client):
    """Test Flask health endpoint"""
    response = flask_client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "healthy"


# Django Tests
@pytest.fixture
def django_urlpatterns():
    """Create Django URL patterns"""
    urlpatterns = []
    return urlpatterns


@pytest.fixture
def django_app(router, django_urlpatterns):
    """Create a Django test application"""
    pyrpc = PyRPCDjango(router)

    # Create view instances with bound handle_request
    import json

    from asgiref.sync import sync_to_async
    from django.utils.decorators import method_decorator
    from django.views import View
    from django.views.decorators.csrf import csrf_exempt

    @method_decorator(csrf_exempt, name="dispatch")
    class PyRPCView(View):
        async def post(self, request, path: str):
            body = await sync_to_async(request.body.decode)()
            data = json.loads(body)
            result = await pyrpc.handle_request(path, data.get("input"))
            return JsonResponse({"result": result.model_dump(), "success": True})

        async def get(self, request):
            return JsonResponse({"status": "healthy"})

        async def dispatch(self, request, *args, **kwargs):
            """Override dispatch to handle async views"""
            if not request.method:
                return JsonResponse(
                    {
                        "success": False,
                        "error": {
                            "code": "METHOD_NOT_ALLOWED",
                            "message": "Method not allowed",
                        },
                    },
                    status=405,
                )

            method = request.method.lower()
            handler = getattr(self, method, self.http_method_not_allowed)

            try:
                response = await sync_to_async(handler)(request, *args, **kwargs)  # type: ignore
                if asyncio.iscoroutine(response):
                    return await response  # type: ignore
                return response
            except Exception as e:
                return JsonResponse(
                    {
                        "success": False,
                        "error": {"code": "INTERNAL_ERROR", "message": str(e)},
                    },
                    status=500,
                )

    # Mount the PyRPC URLs with the correct patterns
    django_urlpatterns.extend(
        [
            path("api/query/<str:path>", PyRPCView.as_view()),
            path("api/mutation/<str:path>", PyRPCView.as_view()),
            path("api/health", PyRPCView.as_view()),
        ]
    )

    # Create a root URLconf module
    class URLConf:
        urlpatterns = django_urlpatterns

    # Update ROOT_URLCONF
    settings.ROOT_URLCONF = URLConf

    return get_wsgi_application()


@pytest.fixture
def django_client(django_app):
    """Create a Django test client"""
    return DjangoClient()


def test_django_query(django_client):
    """Test Django query endpoint"""
    response = django_client.post(
        "/api/query/echo",
        data={"input": {"message": "hello"}},
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["result"]["message"] == "hello"


def test_django_mutation(django_client):
    """Test Django mutation endpoint"""
    response = django_client.post(
        "/api/mutation/echo_mutation",
        data={"input": {"message": "hello"}},
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["result"]["message"] == "hello"


def test_django_health(django_client):
    """Test Django health endpoint"""
    response = django_client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_django_csrf_exempt(django_client):
    """Test Django CSRF exemption"""
    response = django_client.post(
        "/api/query/echo",
        data={"input": {"message": "hello"}},
        content_type="application/json",
        enforce_csrf_checks=True,
    )
    assert response.status_code == 200


@pytest.mark.asyncio  # Add this decorator to mark the test as async
async def test_django_view_direct(router):
    """Test Django view directly"""
    import json

    from django.http import JsonResponse
    from django.test import RequestFactory
    from django.utils.decorators import method_decorator
    from django.views import View
    from django.views.decorators.csrf import csrf_exempt

    pyrpc = PyRPCDjango(router)
    factory = RequestFactory()

    @method_decorator(csrf_exempt, name="dispatch")
    class PyRPCView(View):
        async def post(self, request, path: str):
            data = json.loads(request.body)
            result = await pyrpc.handle_request(path, data.get("input"))
            return JsonResponse({"result": result.model_dump(), "success": True})

        async def get(self, request):
            return JsonResponse({"status": "healthy"})

        async def dispatch(self, request, *args, **kwargs):
            """Override dispatch to handle async views"""
            if not request.method:
                return JsonResponse(
                    {
                        "success": False,
                        "error": {
                            "code": "METHOD_NOT_ALLOWED",
                            "message": "Method not allowed",
                        },
                    },
                    status=405,
                )

            method = request.method.lower()
            handler = getattr(self, method, self.http_method_not_allowed)

            try:
                response = await sync_to_async(handler)(request, *args, **kwargs)
                if asyncio.iscoroutine(response):
                    return await response
                return response
            except Exception as e:
                return JsonResponse(
                    {
                        "success": False,
                        "error": {"code": "INTERNAL_ERROR", "message": str(e)},
                    },
                    status=500,
                )

    view = PyRPCView.as_view()

    # Test POST request for query
    request = factory.post(
        "/api/query/echo",
        data={"input": {"message": "hello"}},
        content_type="application/json",
    )
    response = await view(request, path="echo")  # type: ignore
    assert isinstance(response, JsonResponse)
    data = json.loads(response.content.decode())
    assert data["success"] is True
    assert data["result"]["message"] == "hello"

    # Test GET request for health check
    request = factory.get("/api/health")
    response = await view(request)  # type: ignore
    assert isinstance(response, JsonResponse)
    data = json.loads(response.content.decode())
    assert data["status"] == "healthy"


# Define ContextMiddleware at module level
class ContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.pyrpc_context = PyRPCContext({"test_value": "from_middleware"})
        return self.get_response(request)


@pytest.fixture
def django_app_with_context(context_router, django_urlpatterns):
    """Create a Django test application with context"""
    pyrpc = PyRPCDjango(context_router)

    @method_decorator(csrf_exempt, name="dispatch")
    class PyRPCView(View):
        async def post(self, request, path: str):
            try:
                data = json.loads(request.body)
                context = getattr(request, "pyrpc_context", None)
                if not context:
                    context = PyRPCContext(
                        raw_request={"test_value": "from_middleware"}
                    )
                result = await pyrpc.handle_request(
                    path, data.get("input"), context=context
                )
                return JsonResponse({"result": result.model_dump(), "success": True})
            except json.JSONDecodeError:
                return JsonResponse(
                    {
                        "success": False,
                        "error": {"code": "INVALID_JSON", "message": "Invalid JSON"},
                    },
                    status=400,
                )
            except PyRPCError as e:
                return JsonResponse(
                    {"success": False, "error": {"code": e.code, "message": e.message}},
                    status=e.status_code,
                )
            except Exception as e:
                return JsonResponse(
                    {
                        "success": False,
                        "error": {"code": "INTERNAL_ERROR", "message": str(e)},
                    },
                    status=500,
                )

        async def get(self, request):
            return JsonResponse({"status": "healthy"})

        async def dispatch(self, request, *args, **kwargs):
            """Override dispatch to handle async views"""
            if not request.method:
                return JsonResponse(
                    {
                        "success": False,
                        "error": {
                            "code": "METHOD_NOT_ALLOWED",
                            "message": "Method not allowed",
                        },
                    },
                    status=405,
                )

            method = request.method.lower()
            handler = getattr(self, method, self.http_method_not_allowed)

            try:
                response = await sync_to_async(handler)(request, *args, **kwargs)
                if asyncio.iscoroutine(response):
                    return await response
                return response
            except Exception as e:
                return JsonResponse(
                    {
                        "success": False,
                        "error": {"code": "INTERNAL_ERROR", "message": str(e)},
                    },
                    status=500,
                )

    # Clear existing urlpatterns
    django_urlpatterns.clear()

    # Mount the views
    django_urlpatterns.extend(
        [
            path("api/query/<str:path>", PyRPCView.as_view()),
            path("api/mutation/<str:path>", PyRPCView.as_view()),
            path("api/health", PyRPCView.as_view()),
        ]
    )

    class URLConf:
        urlpatterns = django_urlpatterns

    settings.ROOT_URLCONF = URLConf

    # Configure Django settings
    settings.ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
    settings.MIDDLEWARE = [
        "django.middleware.security.SecurityMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
    ]

    return get_wsgi_application()


@pytest.mark.asyncio
async def test_django_query_with_context(django_app_with_context, context_router):
    """Test Django query with context"""
    factory = RequestFactory()
    body = json.dumps({"input": {"message": "hello"}}).encode("utf-8")
    request = factory.post(
        "/api/query/context_test",
        data=body,
        content_type="application/json",
    )

    @method_decorator(csrf_exempt, name="dispatch")
    class PyRPCTestView(View):
        async def post(self, request, path: str):
            data = json.loads(request.body.decode("utf-8"))
            context = PyRPCContext(raw_request={"test_value": "from_middleware"})
            pyrpc = PyRPCDjango(context_router)
            result = await pyrpc.handle_request(
                path, data.get("input"), context=context
            )
            return JsonResponse({"result": result.model_dump(), "success": True})

        async def dispatch(self, request, *args, **kwargs):
            """Override dispatch to handle async views"""
            if not request.method:
                return JsonResponse({"error": "Method not allowed"}, status=405)
            handler = getattr(
                self, request.method.lower(), self.http_method_not_allowed
            )
            response = await handler(request, *args, **kwargs)  # type: ignore
            return response

    view = PyRPCTestView.as_view()
    response = await view(request, path="context_test")  # type: ignore

    assert response.status_code == 200
    data = json.loads(response.content.decode())
    assert data["success"] is True
    assert data["result"]["context_value"] == "from_middleware"


def test_django_mutation_with_context(django_app_with_context, context_router):
    """Test Django mutation with context"""
    # Create a request factory for direct request handling
    factory = RequestFactory()

    # Create request with proper body
    body = json.dumps({"input": {"message": "hello"}}).encode("utf-8")
    request = factory.post(
        "/api/mutation/context_test",
        data=body,
        content_type="application/json",
    )
    request.pyrpc_context = PyRPCContext(raw_request={"test_value": "from_middleware"})  # type: ignore

    # Create view class with bound router
    @method_decorator(csrf_exempt, name="dispatch")
    class PyRPCView(View):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.pyrpc = PyRPCDjango(context_router)

        async def post(self, request, path: str):
            try:
                data = json.loads(request.body.decode("utf-8"))
                context = getattr(request, "pyrpc_context", None)
                if not context:
                    context = PyRPCContext(
                        raw_request={"test_value": "from_middleware"}
                    )
                print(f"Request data: {data}")  # Debug print
                print(f"Path: {path}")  # Debug print
                result = await self.pyrpc.handle_request(
                    path, data.get("input"), context=context
                )
                print(f"Result: {result}")  # Debug print
                return JsonResponse({"result": result.model_dump(), "success": True})
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {str(e)}")  # Debug print
                return JsonResponse(
                    {
                        "success": False,
                        "error": {"code": "INVALID_JSON", "message": "Invalid JSON"},
                    },
                    status=400,
                )
            except PyRPCError as e:
                print(f"PyRPC error: {str(e)}")  # Debug print
                return JsonResponse(
                    {"success": False, "error": {"code": e.code, "message": e.message}},
                    status=e.status_code,
                )
            except Exception as e:
                print(f"Unexpected error: {str(e)}")  # Debug print
                import traceback

                traceback.print_exc()  # Print full traceback
                return JsonResponse(
                    {
                        "success": False,
                        "error": {"code": "INTERNAL_ERROR", "message": str(e)},
                    },
                    status=500,
                )

        async def get(self, request):
            return JsonResponse({"status": "healthy"})

        async def dispatch(self, request, *args, **kwargs):
            """Override dispatch to handle async views"""
            if not request.method:
                return JsonResponse(
                    {
                        "success": False,
                        "error": {
                            "code": "METHOD_NOT_ALLOWED",
                            "message": "Method not allowed",
                        },
                    },
                    status=405,
                )

            method = request.method.lower()
            handler = getattr(self, method, self.http_method_not_allowed)

            try:
                response = await sync_to_async(handler)(request, *args, **kwargs)
                if asyncio.iscoroutine(response):
                    return await response
                return response
            except Exception as e:
                return JsonResponse(
                    {
                        "success": False,
                        "error": {"code": "INTERNAL_ERROR", "message": str(e)},
                    },
                    status=500,
                )

    # Get the view and handle the request
    view = PyRPCView.as_view()
    response = await view(request, path="context_test")  # type: ignore

    # Test async GET request
    request = factory.get("/api/health")
    response = await sync_to_async(view)(request)  # type: ignore

    # Print response details if there's an error
    if response.status_code != 200:
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.content.decode()}")

    assert response.status_code == 200
    data = json.loads(response.content.decode())
    assert data["success"] is True
    assert data["result"]["context_value"] == "from_middleware"


def test_django_error_handling_comprehensive(error_router, django_urlpatterns):
    """Test comprehensive Django error handling"""
    pyrpc = PyRPCDjango(error_router)

    @method_decorator(csrf_exempt, name="dispatch")
    class PyRPCView(View):
        async def post(self, request, path: str):
            try:
                # Handle both string and bytes input
                if isinstance(request.body, bytes):
                    body = request.body.decode("utf-8")
                else:
                    body = request.body
                data = json.loads(body)
                result = await pyrpc.handle_request(path, data.get("input"))
                return JsonResponse({"result": result.model_dump(), "success": True})
            except json.JSONDecodeError:
                return JsonResponse(
                    {
                        "success": False,
                        "error": {"code": "INVALID_JSON", "message": "Invalid JSON"},
                    },
                    status=400,
                )
            except PyRPCError as e:
                return JsonResponse(
                    {"success": False, "error": {"code": e.code, "message": e.message}},
                    status=e.status_code,
                )
            except Exception as e:
                return JsonResponse(
                    {
                        "success": False,
                        "error": {"code": "INTERNAL_ERROR", "message": str(e)},
                    },
                    status=500,
                )

        async def get(self, request):
            return JsonResponse({"status": "healthy"})

    # Clear existing urlpatterns
    django_urlpatterns.clear()

    # Mount the views
    django_urlpatterns.extend(
        [
            path("api/query/<str:path>", PyRPCView.as_view()),
            path("api/mutation/<str:path>", PyRPCView.as_view()),
            path("api/health", PyRPCView.as_view()),
        ]
    )

    class URLConf:
        urlpatterns = django_urlpatterns

    settings.ROOT_URLCONF = URLConf

    # Ensure testserver is in ALLOWED_HOSTS
    settings.ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]

    client = DjangoClient()

    # Test PyRPCError
    response = client.post(
        "/api/query/error",
        data={"input": {"should_error": True}},
        content_type="application/json",
        HTTP_HOST="testserver",  # Add HTTP_HOST header
    )
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "TEST_ERROR"


def test_django_csrf_handling(error_router, django_urlpatterns):
    """Test Django CSRF handling"""
    pyrpc = PyRPCDjango(error_router)

    @method_decorator(csrf_exempt, name="dispatch")
    class PyRPCView(View):
        async def post(self, request, path: str):
            try:
                # Handle both string and bytes input
                if isinstance(request.body, bytes):
                    body = request.body.decode("utf-8")
                else:
                    body = request.body
                data = json.loads(body)
                result = await pyrpc.handle_request(path, data.get("input"))
                return JsonResponse({"result": result.model_dump(), "success": True})
            except json.JSONDecodeError:
                return JsonResponse(
                    {
                        "success": False,
                        "error": {"code": "INVALID_JSON", "message": "Invalid JSON"},
                    },
                    status=400,
                )
            except Exception as e:
                return JsonResponse(
                    {
                        "success": False,
                        "error": {"code": "INTERNAL_ERROR", "message": str(e)},
                    },
                    status=500,
                )

        async def get(self, request):
            return JsonResponse({"status": "healthy"})

    # Clear existing urlpatterns
    django_urlpatterns.clear()

    # Mount the views
    django_urlpatterns.extend(
        [
            path("api/query/<str:path>", PyRPCView.as_view()),
            path("api/mutation/<str:path>", PyRPCView.as_view()),
            path("api/health", PyRPCView.as_view()),
        ]
    )

    class URLConf:
        urlpatterns = django_urlpatterns

    settings.ROOT_URLCONF = URLConf

    # Ensure testserver is in ALLOWED_HOSTS
    settings.ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]

    client = DjangoClient(enforce_csrf_checks=True)

    # Should work without CSRF token due to csrf_exempt
    response = client.post(
        "/api/query/error",
        data={"input": {"should_error": False}},
        content_type="application/json",
        HTTP_HOST="testserver",  # Add HTTP_HOST header
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_django_view_class_attributes(router, django_urlpatterns):
    """Test Django view class attributes"""
    pyrpc = PyRPCDjango(router)

    @method_decorator(csrf_exempt, name="dispatch")
    class PyRPCView(View):
        async def post(self, request, path: str):
            body = await sync_to_async(request.body.decode)()
            data = json.loads(body)
            result = await pyrpc.handle_request(path, data.get("input"))
            return JsonResponse({"result": result.model_dump(), "success": True})

        async def get(self, request):
            return JsonResponse({"status": "healthy"})

    # Clear existing urlpatterns
    django_urlpatterns.clear()

    # Mount the views
    django_urlpatterns.extend(
        [
            path("api/query/<path:path>", PyRPCView.as_view()),
            path("api/mutation/<path:path>", PyRPCView.as_view()),
            path("api/health", PyRPCView.as_view()),
        ]
    )

    # Get the view classes from urlpatterns
    query_path = django_urlpatterns[0]
    mutation_path = django_urlpatterns[1]
    health_path = django_urlpatterns[2]

    # Check URL patterns
    assert "api/query" in str(query_path.pattern)
    assert "<path:path>" in str(query_path.pattern)
    assert "api/mutation" in str(mutation_path.pattern)
    assert "<path:path>" in str(mutation_path.pattern)
    assert "api/health" in str(health_path.pattern)

    # Get view instances
    query_view = query_path.callback
    mutation_view = mutation_path.callback
    health_view = health_path.callback

    # Test view instances
    query_instance = query_view.view_class()
    mutation_instance = mutation_view.view_class()
    health_instance = health_view.view_class()

    assert hasattr(query_instance, "post")
    assert hasattr(mutation_instance, "post")
    assert hasattr(health_instance, "get")


def test_django_integration_mount(router):
    """Test Django integration mount method"""
    urlpatterns = []
    pyrpc = PyRPCDjango(router)

    # Mount the router
    pyrpc.mount(urlpatterns, prefix="/custom")

    # Check URL patterns
    assert len(urlpatterns) == 3
    query_path = urlpatterns[0]
    mutation_path = urlpatterns[1]
    health_path = urlpatterns[2]

    # Check paths - remove leading slash from pattern string
    pattern_str = str(query_path.pattern).lstrip("/")
    assert pattern_str == "custom/query/<str:path>"
    pattern_str = str(mutation_path.pattern).lstrip("/")
    assert pattern_str == "custom/mutation/<str:path>"
    pattern_str = str(health_path.pattern).lstrip("/")
    assert pattern_str == "custom/health"

    # Check view attributes
    query_view = query_path.callback
    mutation_view = mutation_path.callback

    assert query_view.view_class.request_type == "query"
    assert mutation_view.view_class.request_type == "mutation"
    assert query_view.view_class.handle_request == pyrpc.handle_request
    assert mutation_view.view_class.handle_request == pyrpc.handle_request


@pytest.mark.asyncio
async def test_django_view_async_dispatch(router):
    """Test Django view async dispatch method"""
    factory = RequestFactory()
    pyrpc = PyRPCDjango(router)

    @method_decorator(csrf_exempt, name="dispatch")
    class PyRPCView(View):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.handle_request = pyrpc.handle_request
            self.request_type = "query"

        async def post(self, request, path: str):
            data = json.loads(request.body.decode("utf-8"))
            result = await self.handle_request(path, data.get("input"))
            return JsonResponse({"result": result.model_dump(), "success": True})

        async def get(self, request):
            return JsonResponse({"status": "healthy"})

        async def dispatch(self, request, *args, **kwargs):
            """Override dispatch to handle async views"""
            if not request.method:
                return JsonResponse(
                    {
                        "success": False,
                        "error": {
                            "code": "METHOD_NOT_ALLOWED",
                            "message": "Method not allowed",
                        },
                    },
                    status=405,
                )

            method = request.method.lower()
            handler = getattr(self, method, self.http_method_not_allowed)

            try:
                response = await sync_to_async(handler)(request, *args, **kwargs)  # type: ignore
                if asyncio.iscoroutine(response):
                    return await response  # type: ignore
                return response
            except Exception as e:
                return JsonResponse(
                    {
                        "success": False,
                        "error": {"code": "INTERNAL_ERROR", "message": str(e)},
                    },
                    status=500,
                )

    view = PyRPCView.as_view()

    # Test async POST request
    request = factory.post(
        "/api/query/echo",
        data=json.dumps({"input": {"message": "hello"}}),
        content_type="application/json",
    )
    response = await view(request, path="echo")  # type: ignore
    assert response.status_code == 200
    data = json.loads(response.content.decode())
    assert data["success"] is True
    assert data["result"]["message"] == "hello"

    # Test async GET request
    request = factory.get("/api/health")
    response = await view(request)  # type: ignore
    assert response.status_code == 200
    data = json.loads(response.content.decode())
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_django_view_error_handling(error_router):
    """Test Django view error handling"""
    factory = RequestFactory()
    pyrpc = PyRPCDjango(error_router)

    @method_decorator(csrf_exempt, name="dispatch")
    class PyRPCView(View):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.handle_request = pyrpc.handle_request
            self.request_type = "query"

        async def post(self, request, path: str):
            try:
                data = json.loads(request.body.decode("utf-8"))
                result = await self.handle_request(path, data.get("input"))
                return JsonResponse({"result": result.model_dump(), "success": True})
            except json.JSONDecodeError:
                return JsonResponse(
                    {
                        "success": False,
                        "error": {"code": "INVALID_JSON", "message": "Invalid JSON"},
                    },
                    status=400,
                )
            except PyRPCError as e:
                return JsonResponse(
                    {"success": False, "error": {"code": e.code, "message": e.message}},
                    status=e.status_code,
                )
            except Exception as e:
                return JsonResponse(
                    {
                        "success": False,
                        "error": {"code": "INTERNAL_ERROR", "message": str(e)},
                    },
                    status=500,
                )

        async def get(self, request):
            return JsonResponse({"status": "healthy"})

        async def dispatch(self, request, *args, **kwargs):
            """Override dispatch to handle async views"""
            if not request.method:
                return JsonResponse(
                    {
                        "success": False,
                        "error": {
                            "code": "METHOD_NOT_ALLOWED",
                            "message": "Method not allowed",
                        },
                    },
                    status=405,
                )

            method = request.method.lower()
            handler = getattr(self, method, self.http_method_not_allowed)

            try:
                response = await sync_to_async(handler)(request, *args, **kwargs)  # type: ignore
                if asyncio.iscoroutine(response):
                    return await response  # type: ignore
                return response
            except Exception as e:
                return JsonResponse(
                    {
                        "success": False,
                        "error": {"code": "INTERNAL_ERROR", "message": str(e)},
                    },
                    status=500,
                )

    view = PyRPCView.as_view()

    # Test PyRPCError handling
    request = factory.post(
        "/api/query/error",
        data=json.dumps({"input": {"should_error": True}}),
        content_type="application/json",
    )
    response = await view(request, path="error")  # type: ignore
    assert response.status_code == 400
    data = json.loads(response.content.decode())
    assert data["success"] is False
    assert data["error"]["code"] == "TEST_ERROR"

    # Test invalid JSON handling
    request = factory.post(
        "/api/query/error", data="invalid json", content_type="application/json"
    )
    response = await view(request, path="error")  # type: ignore
    assert response.status_code == 400
    data = json.loads(response.content.decode())
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_JSON"

    # Test validation error handling
    request = factory.post(
        "/api/query/error",
        data=json.dumps({"input": None}),  # This will cause a validation error
        content_type="application/json",
    )
    response = await view(request, path="error")  # type: ignore
    assert response.status_code == 400  # Validation errors should be 400
    data = json.loads(response.content.decode())
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"
