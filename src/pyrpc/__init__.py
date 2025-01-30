"""
PyRPC - A type-safe RPC framework for Python

PyRPC is a modern, type-safe RPC framework that brings end-to-end type safety
to your Python APIs. It's framework agnostic and works with FastAPI, Flask, Django,
and other Python web frameworks.
"""

from .core import (
    PyRPCRouter,
    PyRPCError,
    ProcedureDef,
    ProcedureBuilder,
)
from .client import (
    PyRPCClient,
    ClientConfig,
    PyRPCClientError,
)
from .context import (
    PyRPCContext,
    MiddlewareFunction,
    MiddlewareBuilder,
)
from .integrations import (
    PyRPCFastAPI,
    PyRPCFlask,
    PyRPCDjango,
)

# Version of the pyrpc package
__version__ = "0.1.0"

__all__ = [
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
    "PyRPCFastAPI",
    "PyRPCFlask",
    "PyRPCDjango",
] 