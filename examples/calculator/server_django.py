from typing import List

# Configure Django settings
from django.conf import settings
from django.core.asgi import get_asgi_application
from models import (
    CalculationInput,
    CalculationOutput,
    GetHistoryInput,
    HistoryEntry,
    HistoryResponse,
)
from pydantic import ValidationError

from pyrpc import MiddlewareFunction, PyRPCContext, PyRPCDjango, PyRPCError, PyRPCRouter

if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY="dev-key-for-example",
        ROOT_URLCONF=__name__,
        ALLOWED_HOSTS=["*"],
        MIDDLEWARE=[
            "django.middleware.common.CommonMiddleware",
        ],
    )


# Create validation middleware
class ValidationMiddleware(MiddlewareFunction):
    async def __call__(self, ctx: PyRPCContext, next):
        try:
            return await next(ctx)
        except ValidationError as e:
            raise PyRPCError(code="VALIDATION_ERROR", message=str(e)) from e


# Create router
router = PyRPCRouter()
router.middleware.use(ValidationMiddleware())

# In-memory storage for calculation history
calculation_history: List[HistoryEntry] = []


def record_calculation(operation: str, a: float, b: float, result: float):
    """Record a calculation in history"""
    entry = HistoryEntry(operation=operation, a=a, b=b, result=result)
    calculation_history.append(entry)
    return entry


@router.query("add")
def add(input: CalculationInput) -> CalculationOutput:
    """Add two numbers"""
    try:
        result = input.a + input.b
        record_calculation("add", input.a, input.b, result)
        return CalculationOutput(result=result, operation="add")
    except ValueError as e:
        raise PyRPCError(code="VALIDATION_ERROR", message=str(e)) from e


@router.query("subtract")
def subtract(input: CalculationInput) -> CalculationOutput:
    """Subtract two numbers"""
    try:
        result = input.a - input.b
        record_calculation("subtract", input.a, input.b, result)
        return CalculationOutput(result=result, operation="subtract")
    except ValueError as e:
        raise PyRPCError(code="VALIDATION_ERROR", message=str(e)) from e


@router.query("multiply")
def multiply(input: CalculationInput) -> CalculationOutput:
    """Multiply two numbers"""
    try:
        result = input.a * input.b
        record_calculation("multiply", input.a, input.b, result)
        return CalculationOutput(result=result, operation="multiply")
    except ValueError as e:
        raise PyRPCError(code="VALIDATION_ERROR", message=str(e)) from e


@router.query("divide")
def divide(input: CalculationInput) -> CalculationOutput:
    """Divide two numbers"""
    try:
        if input.b == 0:
            raise PyRPCError(code="INVALID_INPUT", message="Cannot divide by zero")
        result = input.a / input.b
        record_calculation("divide", input.a, input.b, result)
        return CalculationOutput(result=result, operation="divide")
    except ValueError as e:
        raise PyRPCError(code="VALIDATION_ERROR", message=str(e)) from e


@router.query("history")
def get_history(input: GetHistoryInput) -> HistoryResponse:
    """Get calculation history"""
    try:
        entries = calculation_history[-input.limit :]
        return HistoryResponse(entries=entries)
    except ValueError as e:
        raise PyRPCError(code="VALIDATION_ERROR", message=str(e)) from e


# Create Django app
pyrpc = PyRPCDjango(router)

# URL configuration
urlpatterns = []
pyrpc.mount(urlpatterns)

# Create ASGI application
application = get_asgi_application()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(application, host="0.0.0.0", port=8000)
