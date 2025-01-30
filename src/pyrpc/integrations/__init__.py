"""Framework integrations for PyRPC"""

from .base import BasePyRPCIntegration

# Optional imports based on installed packages
try:
    from .fastapi_integration import PyRPCFastAPI
except ImportError:
    PyRPCFastAPI = None

try:
    from .flask_integration import PyRPCFlask
except ImportError:
    PyRPCFlask = None

try:
    from .django_integration import PyRPCDjango
except ImportError:
    PyRPCDjango = None

__all__ = [
    "BasePyRPCIntegration",
    "PyRPCFastAPI",
    "PyRPCFlask",
    "PyRPCDjango",
]
