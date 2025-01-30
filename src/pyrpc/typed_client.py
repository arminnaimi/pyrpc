"""Type-safe client implementation for PyRPC"""

from typing import TypeVar, cast

from .client import ClientConfig, PyRPCClient
from .typed_router import Router

T = TypeVar("T")


def create_caller(router: Router[T], base_url: str) -> T:
    """Create a type-safe client from a router"""
    client = PyRPCClient(ClientConfig(base_url=base_url))

    class Client(router.api_cls):
        def __getattr__(self, name: str):
            if name not in router.procedures:
                raise AttributeError(f"No procedure named {name}")

            async def caller(input):
                procedure = client.caller(name)
                return await procedure(input)  # type: ignore

            return caller

    return cast(T, Client())
