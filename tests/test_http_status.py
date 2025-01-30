"""Tests for HTTP status codes and error handling in PyRPC"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from pyrpc import PyRPCError, PyRPCFastAPI, PyRPCRouter


# Test models
class DivideInput(BaseModel):
    numerator: float
    denominator: float = Field(..., description="Cannot be zero")


class DivideOutput(BaseModel):
    result: float


class AuthInput(BaseModel):
    token: str


class EmptyInput(BaseModel):
    """Empty input model for endpoints that don't need input"""

    pass


# Test fixtures
@pytest.fixture
def router():
    """Create a test router with error-prone procedures"""
    router = PyRPCRouter()

    @router.query("divide")
    def divide(input: DivideInput) -> DivideOutput:
        if input.denominator == 0:
            raise PyRPCError(
                code="BAD_REQUEST",
                message="Division by zero is not allowed",
                status_code=400,
            )
        return DivideOutput(result=input.numerator / input.denominator)

    @router.query("protected")
    def protected(input: AuthInput) -> dict:
        if input.token != "valid_token":
            raise PyRPCError(
                code="UNAUTHORIZED", message="Invalid token", status_code=401
            )
        return {"data": "secret"}

    @router.query("not_implemented")
    def not_implemented(input: EmptyInput) -> dict:
        error = PyRPCError(
            code="NOT_IMPLEMENTED",
            message="This feature is not implemented yet",
            status_code=501,
        )
        # Print debug info
        print(f"Error created with: code={error.code}, status_code={error.status_code}")
        print(f"Error attributes: {vars(error)}")
        raise error

    @router.query("server_error")
    def server_error(_: BaseModel) -> dict:
        raise Exception("Unexpected server error")

    return router


@pytest.fixture
def app(router):
    """Create a FastAPI test application"""
    app = FastAPI()
    pyrpc = PyRPCFastAPI(router)
    pyrpc.mount(app)
    return app


@pytest.fixture
def client(app):
    """Create a test client"""
    return TestClient(app)


# Test cases
def test_successful_request(client):
    """Test successful request returns 200"""
    response = client.post(
        "/api/query/divide", json={"input": {"numerator": 10, "denominator": 2}}
    )
    assert response.status_code == 200
    assert response.json() == {"result": {"result": 5.0}, "success": True}


def test_bad_request(client):
    """Test bad request (400) status code"""
    response = client.post(
        "/api/query/divide", json={"input": {"numerator": 10, "denominator": 0}}
    )
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "BAD_REQUEST"
    assert "Division by zero" in data["error"]["message"]


def test_unauthorized(client):
    """Test unauthorized (401) status code"""
    response = client.post(
        "/api/query/protected", json={"input": {"token": "invalid_token"}}
    )
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "UNAUTHORIZED"
    assert "Invalid token" in data["error"]["message"]


def test_not_found(client):
    """Test not found (404) status code"""
    response = client.post("/api/query/nonexistent", json={"input": {}})
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "NOT_FOUND"


def test_validation_error(client):
    """Test validation error (400) status code"""
    response = client.post("/api/query/divide", json={"input": {"wrong_field": 10}})
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_not_implemented(client):
    """Test not implemented (501) status code"""
    response = client.post("/api/query/not_implemented", json={"input": {}})
    assert response.status_code == 501
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "NOT_IMPLEMENTED"
    assert "not implemented yet" in data["error"]["message"].lower()


def test_server_error(client):
    """Test internal server error (500) status code"""
    response = client.post("/api/query/server_error", json={"input": {}})
    assert response.status_code == 500
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"


def test_method_not_allowed(client):
    """Test method not allowed (405) status code"""
    response = client.get("/api/query/divide")
    assert response.status_code == 405


def test_malformed_json(client):
    """Test malformed JSON request (400) status code"""
    response = client.post(
        "/api/query/divide",
        content=b"invalid json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "error" in data


def test_integration_error_handling(client):
    """Test error handling in integrations"""
    # Test invalid input
    response = client.post(
        "/api/query/divide", json={"input": {"wrong_field": "value"}}
    )
    assert response.status_code == 400
    assert response.json()["success"] is False
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"

    # Test not found
    response = client.post("/api/query/non_existent", json={"input": {}})
    assert response.status_code == 404
    assert response.json()["success"] is False
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_fastapi_custom_error_handler(client):
    """Test custom error handler in FastAPI integration"""
    # Test with a custom error that doesn't have a status code
    response = client.post("/api/query/server_error", json={"input": {}})
    assert response.status_code == 500
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"


def test_fastapi_cors_config(router):
    """Test CORS configuration in FastAPI integration"""
    app = FastAPI()
    pyrpc = PyRPCFastAPI(
        router,
        cors_config={
            "allow_origins": ["http://localhost:3000"],
            "allow_methods": ["POST"],
            "allow_headers": ["*"],
        },
    )
    pyrpc.mount(app)
    client = TestClient(app)

    # Test CORS preflight request
    response = client.options(
        "/api/query/divide",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert "POST" in response.headers["access-control-allow-methods"]


def test_fastapi_custom_prefix(router):
    """Test custom prefix configuration in FastAPI integration"""
    app = FastAPI()
    pyrpc = PyRPCFastAPI(router, prefix="/custom")
    pyrpc.mount(app)
    client = TestClient(app)

    # Test with custom prefix
    response = client.post(
        "/custom/query/divide", json={"input": {"numerator": 10, "denominator": 2}}
    )
    assert response.status_code == 200
    assert response.json()["result"]["result"] == 5.0

    # Test old prefix should not work
    response = client.post(
        "/api/query/divide", json={"input": {"numerator": 10, "denominator": 2}}
    )
    assert response.status_code == 404


def test_fastapi_middleware_error(router):
    """Test middleware error handling in FastAPI integration"""
    app = FastAPI()
    pyrpc = PyRPCFastAPI(router)

    # Add a middleware that raises an error
    @app.middleware("http")
    async def error_middleware(request, call_next):
        raise PyRPCError(
            code="MIDDLEWARE_ERROR", message="Middleware error", status_code=500
        )

    pyrpc.mount(app)
    client = TestClient(app)

    response = client.post(
        "/api/query/divide", json={"input": {"numerator": 10, "denominator": 2}}
    )
    assert response.status_code == 500
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "MIDDLEWARE_ERROR"


def test_fastapi_invalid_content_type(client):
    """Test request with invalid content type"""
    response = client.post(
        "/api/query/divide", content=b"not json", headers={"Content-Type": "text/plain"}
    )
    assert response.status_code == 415
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "UNSUPPORTED_MEDIA_TYPE"
