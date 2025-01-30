"""PyRPC test fixtures"""
import pytest
from pydantic import BaseModel
from pyrpc import PyRPCRouter, PyRPCContext, MiddlewareFunction
import django
from django.conf import settings

# Configure Django settings
def pytest_configure():
    settings.configure(
        DEBUG=True,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:'
            }
        },
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
        ],
        MIDDLEWARE=[],
        ROOT_URLCONF=[],
        SECRET_KEY='test-key',
        USE_TZ=True,
        TIME_ZONE='UTC',
        DEFAULT_CHARSET='utf-8',
    )
    django.setup()

# Test models
class HelloInput(BaseModel):
    name: str

class HelloOutput(BaseModel):
    message: str

class UserInput(BaseModel):
    id: int

class UserOutput(BaseModel):
    id: int
    name: str
    email: str

# Test middleware
class TestMiddleware:
    """Test middleware implementation"""
    def __init__(self):
        self.calls = []

    async def __call__(self, ctx: PyRPCContext, next):
        self.calls.append("before")
        result = await next(ctx)
        self.calls.append("after")
        return result

@pytest.fixture
def router():
    """Create a test router with some procedures"""
    router = PyRPCRouter()

    @router.query("hello")
    def hello(input: HelloInput) -> HelloOutput:
        return HelloOutput(message=f"Hello {input.name}!")

    @router.query("user")
    def get_user(input: UserInput) -> UserOutput:
        return UserOutput(
            id=input.id,
            name="Test User",
            email="test@example.com"
        )

    return router

@pytest.fixture
def middleware():
    """Create a test middleware"""
    return TestMiddleware()

@pytest.fixture
def context():
    """Create a test context"""
    return PyRPCContext(raw_request={"test": True}) 