"""Tests for PyRPC client functionality"""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from httpx import Request, Response

from pyrpc import ClientConfig, PyRPCClient, PyRPCClientError
from tests.conftest import HelloInput, HelloOutput, UserInput, UserOutput


def create_response(status_code: int, json_data: dict) -> Response:
    """Create a mock Response with request information"""
    request = Request("POST", "http://test")
    return Response(status_code=status_code, json=json_data, request=request)


@pytest.fixture
def mock_client():
    """Create a mock HTTP client"""
    with patch("httpx.AsyncClient") as mock:
        mock.return_value.post = AsyncMock()
        yield mock.return_value


@pytest.fixture
def client(mock_client):
    """Create a PyRPC client with mocked HTTP client"""
    config = ClientConfig(base_url="http://test")
    client = PyRPCClient(config)
    client.client = mock_client
    return client


async def test_client_query(client, mock_client):
    """Test client query execution"""
    mock_client.post.return_value = create_response(
        200, {"result": {"message": "Hello World!"}, "success": True}
    )

    caller = client.caller("test")
    hello = caller.procedure("hello", HelloInput, HelloOutput)

    result = await hello({"name": "World"})
    assert isinstance(result, HelloOutput)
    assert result.message == "Hello World!"

    mock_client.post.assert_called_once_with(
        "/query/test.hello", json={"input": {"name": "World"}}
    )


async def test_client_mutation(client, mock_client):
    """Test client mutation execution"""
    mock_client.post.return_value = create_response(
        200,
        {
            "result": {"id": 1, "name": "Test User", "email": "test@example.com"},
            "success": True,
        },
    )

    caller = client.caller("users")
    create_user = caller.procedure("create", UserInput, UserOutput, is_mutation=True)

    result = await create_user({"id": 1})
    assert isinstance(result, UserOutput)
    assert result.id == 1
    assert result.name == "Test User"

    mock_client.post.assert_called_once_with(
        "/mutation/users.create", json={"input": {"id": 1}}
    )


async def test_client_error_handling(client, mock_client):
    """Test client error handling"""
    mock_client.post.return_value = create_response(
        200,
        {"error": {"code": "NOT_FOUND", "message": "User not found"}, "success": False},
    )

    caller = client.caller("users")
    get_user = caller.procedure("get", UserInput, UserOutput)

    with pytest.raises(PyRPCClientError) as exc:
        await get_user({"id": 1})

    assert exc.value.code == "NOT_FOUND"
    assert exc.value.message == "User not found"


async def test_client_network_error(client, mock_client):
    """Test client network error handling"""
    mock_client.post.side_effect = httpx.NetworkError("Network error")

    caller = client.caller("test")
    hello = caller.procedure("hello", HelloInput, HelloOutput)

    with pytest.raises(PyRPCClientError) as exc:
        await hello({"name": "World"})

    assert exc.value.code == "NETWORK_ERROR"
    assert "Network error" in str(exc.value)


async def test_client_validation(client, mock_client):
    """Test client input validation"""
    caller = client.caller("test")
    hello = caller.procedure("hello", HelloInput, HelloOutput)

    with pytest.raises(Exception):
        await hello({"wrong_field": "value"})


async def test_client_type_safety(client, mock_client):
    """Test client type safety"""
    mock_client.post.return_value = create_response(
        200, {"result": {"message": "Hello World!"}, "success": True}
    )

    caller = client.caller("test")
    hello = caller.procedure("hello", HelloInput, HelloOutput)

    # Test with model instance
    input_model = HelloInput(name="World")
    result = await hello(input_model)
    assert isinstance(result, HelloOutput)

    # Test with dict
    result = await hello({"name": "World"})
    assert isinstance(result, HelloOutput)
