"""FastAPI integration for PyRPC"""
from typing import Any, Optional
from fastapi import FastAPI, APIRouter, Response
from ..core import PyRPCRouter, PyRPCError
from ..context import PyRPCContext
from .base import BasePyRPCIntegration

class PyRPCFastAPI(BasePyRPCIntegration):
    """FastAPI integration for PyRPC"""
    def __init__(self, router: PyRPCRouter):
        super().__init__(router)
        self.api_router = APIRouter()

    async def handle_request(self, path: str, input_data: Any, context: Optional[PyRPCContext] = None):
        """Handle FastAPI request"""
        return await self.router.handle(path, input_data, context)

    def mount(self, app: FastAPI, prefix: str = "/trpc"):
        """Mount PyRPC routes on FastAPI app"""
        @self.api_router.post("/query/{path:path}")
        async def handle_query(path: str, request_data: dict, response: Response):
            try:
                result = await self.handle_request(path, request_data.get("input"))
                return {
                    "result": result.model_dump(),
                    "success": True
                }
            except PyRPCError as e:
                response.status_code = e.status_code
                return {
                    "error": {"code": e.code, "message": str(e)},
                    "success": False
                }
            except Exception as e:
                response.status_code = 500
                return {
                    "error": {"code": "INTERNAL_SERVER_ERROR", "message": str(e)},
                    "success": False
                }

        @self.api_router.post("/mutation/{path:path}")
        async def handle_mutation(path: str, request_data: dict, response: Response):
            try:
                result = await self.handle_request(path, request_data.get("input"))
                return {
                    "result": result.model_dump(),
                    "success": True
                }
            except PyRPCError as e:
                response.status_code = e.status_code
                return {
                    "error": {"code": e.code, "message": str(e)},
                    "success": False
                }
            except Exception as e:
                response.status_code = 500
                return {
                    "error": {"code": "INTERNAL_SERVER_ERROR", "message": str(e)},
                    "success": False
                }

        @self.api_router.get("/health")
        async def health_check():
            return {"status": "healthy"}

        app.include_router(self.api_router, prefix=prefix)

# Example usage:
# app = FastAPI()
# router = PyRPCRouter()
# trpc = PyRPCFastAPI(router)
# trpc.mount(app) 