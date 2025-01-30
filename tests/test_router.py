"""Tests for PyRPC router functionality"""

import pytest

from pyrpc import PyRPCError, PyRPCRouter
from tests.conftest import HelloInput, HelloOutput, UserInput, UserOutput


async def test_router_query(router):
    """Test basic query functionality"""
    result = await router.handle("hello", {"name": "World"})
    assert result.message == "Hello World!"


async def test_router_validation(router):
    """Test input validation"""
    with pytest.raises(PyRPCError) as exc:
        await router.handle("hello", {"wrong_field": "value"})
    assert exc.value.code == "VALIDATION_ERROR"
    assert exc.value.status_code == 400


async def test_router_not_found(router):
    """Test handling of non-existent procedures"""
    with pytest.raises(PyRPCError) as exc:
        await router.handle("non_existent", {"name": "World"})
    assert exc.value.code == "NOT_FOUND"


async def test_nested_routers():
    """Test nested router functionality"""
    parent = PyRPCRouter()
    child = PyRPCRouter()

    @child.query("hello")
    def hello(input: HelloInput) -> HelloOutput:
        return HelloOutput(message=f"Hello {input.name}!")

    parent.merge("child", child)

    result = await parent.handle("child.hello", {"name": "World"})
    assert result.message == "Hello World!"


async def test_middleware(router, middleware):
    """Test middleware execution"""
    router.middleware.use(middleware)

    result = await router.handle("hello", {"name": "World"})

    assert result.message == "Hello World!"
    assert middleware.calls == ["before", "after"]


async def test_multiple_middleware(router):
    """Test multiple middleware execution order"""
    calls = []

    class OrderMiddleware:
        def __init__(self, order: str):
            self.order = order
            self.calls = calls

        async def __call__(self, ctx, next):
            self.calls.append(f"before_{self.order}")
            result = await next(ctx)
            self.calls.append(f"after_{self.order}")
            return result

    router.middleware.use(OrderMiddleware(order="1"))
    router.middleware.use(OrderMiddleware(order="2"))

    await router.handle("hello", {"name": "World"})

    assert calls == ["before_1", "before_2", "after_2", "after_1"]


async def test_context_passing(router, context):
    """Test context is properly passed through the stack"""

    @router.query("context_test")
    def context_test(input: HelloInput, ctx) -> HelloOutput:
        assert ctx.raw_request == {"test": True}
        return HelloOutput(message=f"Hello {input.name}!")

    result = await router.handle("context_test", {"name": "World"}, context)
    assert result.message == "Hello World!"


async def test_mutation(router):
    """Test mutation procedure"""

    @router.mutation("create_user")
    def create_user(input: UserInput) -> UserOutput:
        return UserOutput(id=input.id, name="New User", email="new@example.com")

    result = await router.handle("create_user", {"id": 1})
    assert result.id == 1
    assert result.name == "New User"
