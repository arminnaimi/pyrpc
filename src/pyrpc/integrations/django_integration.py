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

    def mount(self, urlpatterns: list, prefix: str = "/api"):
        """Mount PyRPC routes on Django URL patterns"""
        @method_decorator(csrf_exempt, name='dispatch')
        class PyRPCQueryView(View):
            handle_request = None  # Will be set via as_view
            request_type = "query"  # Set directly on class
            
            async def post(self, request, path: str):
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

            def dispatch(self, request, *args, **kwargs):
                """Override dispatch to handle async views"""
                if not asyncio.iscoroutinefunction(getattr(self, request.method.lower(), None)):
                    return super().dispatch(request, *args, **kwargs)
                async def await_and_return(coroutine):
                    return await coroutine
                return asyncio.run(await_and_return(super().dispatch(request, *args, **kwargs)))

        @method_decorator(csrf_exempt, name='dispatch')
        class PyRPCMutationView(PyRPCQueryView):
            request_type = "mutation"  # Override for mutation view

        @method_decorator(csrf_exempt, name='dispatch')
        class PyRPCHealthView(PyRPCQueryView):
            request_type = None  # Health view doesn't need a request type

        # Create view instances with bound handle_request
        query_view = PyRPCQueryView.as_view()
        query_view.view_class.handle_request = self.handle_request
        
        mutation_view = PyRPCMutationView.as_view()
        mutation_view.view_class.handle_request = self.handle_request
        
        health_view = PyRPCHealthView.as_view()
        health_view.view_class.handle_request = self.handle_request

        # Add URL patterns in the correct order: query, mutation, health
        urlpatterns.extend([
            path(f"{prefix.rstrip('/')}/query/<str:path>", query_view),
            path(f"{prefix.rstrip('/')}/mutation/<str:path>", mutation_view),
            path(f"{prefix.rstrip('/')}/health", health_view),
        ])

# Example usage:
# from django.urls import path
# urlpatterns = []
# router = PyRPCRouter()
# pyrpc = PyRPCDjango(router)
# pyrpc.mount(urlpatterns) 