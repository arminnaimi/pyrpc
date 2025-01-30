"""Flask integration for PyRPC"""

from typing import Any, Optional

from flask import Flask, jsonify, request

from ..context import PyRPCContext
from ..core import PyRPCError, PyRPCRouter
from .base import BasePyRPCIntegration


class PyRPCFlask(BasePyRPCIntegration):
    """Flask integration for PyRPC"""

    def __init__(self, router: PyRPCRouter):
        super().__init__(router)

    async def handle_request(
        self, path: str, input_data: Any, context: Optional[PyRPCContext] = None
    ):
        """Handle Flask request"""
        return await self.router.handle(path, input_data, context)

    def mount(self, app: Flask, prefix: str = "/api"):
        """Mount PyRPC routes on Flask app"""

        @app.post(f"{prefix}/query/<path:path>")
        async def handle_query(path):
            try:
                request_data = request.get_json()
                result = await self.handle_request(path, request_data.get("input"))
                return jsonify({"result": result.model_dump(), "success": True})
            except PyRPCError as e:
                response = jsonify(
                    {"error": {"code": e.code, "message": str(e)}, "success": False}
                )
                response.status_code = e.status_code
                return response
            except Exception as e:
                response = jsonify(
                    {
                        "error": {"code": "INTERNAL_SERVER_ERROR", "message": str(e)},
                        "success": False,
                    }
                )
                response.status_code = 500
                return response

        @app.post(f"{prefix}/mutation/<path:path>")
        async def handle_mutation(path):
            try:
                request_data = request.get_json()
                result = await self.handle_request(path, request_data.get("input"))
                return jsonify({"result": result.model_dump(), "success": True})
            except PyRPCError as e:
                response = jsonify(
                    {"error": {"code": e.code, "message": str(e)}, "success": False}
                )
                response.status_code = e.status_code
                return response
            except Exception as e:
                response = jsonify(
                    {
                        "error": {"code": "INTERNAL_SERVER_ERROR", "message": str(e)},
                        "success": False,
                    }
                )
                response.status_code = 500
                return response

        @app.get(f"{prefix}/health")
        async def health_check():
            return jsonify({"status": "healthy"})


# Example usage:
# app = Flask(__name__)
# router = PyRPCRouter()
# pyrpc = PyRPCFlask(router)
# pyrpc.mount(app)
