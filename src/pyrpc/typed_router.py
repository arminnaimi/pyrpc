"""Type-safe router implementation for PyRPC"""

from typing import Callable, Dict, Generic, Type, TypeVar, get_type_hints

from fastapi import APIRouter

T = TypeVar("T")


class Router(Generic[T]):
    """Type-safe router implementation"""

    def __init__(self, api_cls: Type[T]):
        self.procedures: Dict[str, Callable] = {}
        self.router = APIRouter()
        self.api_cls = api_cls

        # Register methods from API class
        for name, method in api_cls.__dict__.items():
            if not name.startswith("_") and callable(method):
                hints = get_type_hints(method)
                if "input" in hints and "return" in hints:
                    self.procedures[name] = method
                    self.router.add_api_route(
                        f"/{name}",
                        method,
                        methods=["POST"],
                        response_model=hints["return"],
                    )


def t(api_cls: Type[T]) -> Router[T]:
    """Create a new router from an API class"""
    return Router(api_cls)
