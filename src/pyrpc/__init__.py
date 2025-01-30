"""
PyRPC - A type-safe RPC framework for Python

PyRPC is a modern, type-safe RPC framework that brings end-to-end type safety
to your Python APIs. It's framework agnostic and works with FastAPI, Flask, Django,
and other Python web frameworks.
"""

from .client import (
    ClientConfig,
    PyRPCClient,
    PyRPCClientError,
)
from .context import (
    MiddlewareBuilder,
    MiddlewareFunction,
    PyRPCContext,
)
from .core import (
    ProcedureBuilder,
    ProcedureDef,
    PyRPCError,
    PyRPCRouter,
)
from .integrations import (
    PyRPCDjango,
    PyRPCFastAPI,
    PyRPCFlask,
)
from .typed_router import t

# Version of the pyrpc package
__version__ = "0.1.0"

__all__ = [
    # Core functionality
    "PyRPCRouter",
    "PyRPCError",
    "ProcedureDef",
    "ProcedureBuilder",
    "PyRPCClient",
    "ClientConfig",
    "PyRPCClientError",
    "PyRPCContext",
    "MiddlewareFunction",
    "MiddlewareBuilder",
    # Framework integrations
    "PyRPCFastAPI",
    "PyRPCFlask",
    "PyRPCDjango",
    # Type-safe router (new)
    "t",
]
