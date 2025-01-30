"""Base integration class for PyRPC"""
from typing import Any, Optional
from abc import ABC, abstractmethod
from ..core import PyRPCRouter
from ..context import PyRPCContext

class BasePyRPCIntegration(ABC):
    """Base class for framework integrations"""
    def __init__(self, router: PyRPCRouter):
        self.router = router

    @abstractmethod
    async def handle_request(self, path: str, input_data: Any, context: Optional[PyRPCContext] = None):
        """Handle an incoming request"""
        pass

    @abstractmethod
    def mount(self, app: Any, prefix: str = "/trpc"):
        """Mount the PyRPC router to a framework application"""
        pass 