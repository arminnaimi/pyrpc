"""Type-safe client implementation for PyRPC"""
from typing import TypeVar, Type
from .core import PyRPCClient
from .typed_router import Router

T = TypeVar('T')

def create_caller(router: Router[T], base_url: str) -> T:
    """Create a type-safe client from a router"""
    client = PyRPCClient(base_url)
    
    class Client(router.api_cls):
        def __getattr__(self, name: str):
            if name not in router.procedures:
                raise AttributeError(f"No procedure named {name}")
            async def caller(input):
                return await client.call(name, input)
            return caller
            
    return Client() 