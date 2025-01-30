"""Django integration for PyRPC"""
from typing import Any, Optional
from django.urls import path
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json
from ..core import PyRPCRouter, PyRPCError
from ..context import PyRPCContext
from .base import BasePyRPCIntegration
import asyncio

class PyRPCDjango(BasePyRPCIntegration):
    """Django integration for PyRPC"""
    def __init__(self, router: PyRPCRouter):
        super().__init__(router)

    async def handle_request(self, path: str, input_data: Any, context: Optional[PyRPCContext] = None):
        """Handle Django request"""
        return await self.router.handle(path, input_data, context)

    def mount(self, urlpatterns: list, prefix: str = "/trpc"):
        """Mount PyRPC routes on Django URL patterns"""
        @method_decorator(csrf_exempt, name='dispatch')
        class PyRPCView(View):
            async def post(self, request, type: str, path: str):
                try:
                    data = json.loads(request.body)
                    result = await self.handle_request(path, data.get("input"))
                    return JsonResponse({
                        "result": result.model_dump(),
                        "success": True
                    })
                except PyRPCError as e:
                    return JsonResponse({
                        "error": {"code": e.code, "message": str(e)},
                        "success": False
                    }, status=e.status_code)
                except Exception as e:
                    return JsonResponse({
                        "error": {"code": "INTERNAL_SERVER_ERROR", "message": str(e)},
                        "success": False
                    }, status=500)

            async def get(self, request):
                return JsonResponse({"status": "healthy"})

        urlpatterns.extend([
            path(f"{prefix}/query/<path:path>", PyRPCView.as_view(handle_request=self.handle_request)),
            path(f"{prefix}/mutation/<path:path>", PyRPCView.as_view(handle_request=self.handle_request)),
            path(f"{prefix}/health", PyRPCView.as_view()),
        ])

# Example usage:
# from django.urls import path
# urlpatterns = []
# router = PyRPCRouter()
# trpc = PyRPCDjango(router)
# trpc.mount(urlpatterns) 