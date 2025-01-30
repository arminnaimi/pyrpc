"""Framework integrations for PyRPC"""
from typing import Any, Optional
from .core import PyRPCRouter
from .context import PyRPCContext
from fastapi import FastAPI, APIRouter
from flask import Flask
from django.urls import path
from django.http import JsonResponse

class PyRPCFastAPI:
    """FastAPI integration for PyRPC"""
    def __init__(self, router: PyRPCRouter):
        self.router = router
        self.api_router = APIRouter()

    async def handle_request(self, path: str, input_data: Any, context: Optional[PyRPCContext] = None):
        """Handle FastAPI request"""
        return await self.router.handle(path, input_data, context)

    def mount(self, app: FastAPI, prefix: str = "/trpc"):
        """Mount PyRPC routes on FastAPI app"""
        @self.api_router.post("/query/{path:path}")
        async def handle_query(path: str, request_data: dict):
            result = await self.handle_request(path, request_data.get("input"))
            return {"result": result, "success": True}

        @self.api_router.post("/mutation/{path:path}")
        async def handle_mutation(path: str, request_data: dict):
            result = await self.handle_request(path, request_data.get("input"))
            return {"result": result, "success": True}

        @self.api_router.get("/health")
        async def health_check():
            return {"status": "healthy"}

        app.include_router(self.api_router, prefix=prefix)

class PyRPCFlask:
    """Flask integration for PyRPC"""
    def __init__(self, router: PyRPCRouter):
        self.router = router

    async def handle_request(self, path: str, input_data: Any, context: Optional[PyRPCContext] = None):
        """Handle Flask request"""
        return await self.router.handle(path, input_data, context)

    def mount(self, app: Flask, prefix: str = "/trpc"):
        """Mount PyRPC routes on Flask app"""
        @app.post(f"{prefix}/query/<path:path>")
        async def handle_query(path):
            from flask import request
            result = await self.handle_request(path, request.get_json().get("input"))
            return {"result": result, "success": True}

        @app.post(f"{prefix}/mutation/<path:path>")
        async def handle_mutation(path):
            from flask import request
            result = await self.handle_request(path, request.get_json().get("input"))
            return {"result": result, "success": True}

        @app.get(f"{prefix}/health")
        async def health_check():
            return {"status": "healthy"}

class PyRPCDjango:
    """Django integration for PyRPC"""
    def __init__(self, router: PyRPCRouter):
        self.router = router

    async def handle_request(self, path: str, input_data: Any, context: Optional[PyRPCContext] = None):
        """Handle Django request"""
        return await self.router.handle(path, input_data, context)

    def mount(self, urlpatterns: list, prefix: str = "/trpc"):
        """Mount PyRPC routes on Django URL patterns"""
        from django.views import View
        from django.utils.decorators import method_decorator
        from django.views.decorators.csrf import csrf_exempt
        import json

        @method_decorator(csrf_exempt, name='dispatch')
        class PyRPCView(View):
            async def post(self, request, type: str, path: str):
                data = json.loads(request.body)
                result = await self.handle_request(path, data.get("input"))
                return JsonResponse({"result": result, "success": True})

            async def get(self, request):
                return JsonResponse({"status": "healthy"})

        urlpatterns.extend([
            path(f"{prefix}/query/<path:path>", PyRPCView.as_view(handle_request=self.handle_request)),
            path(f"{prefix}/mutation/<path:path>", PyRPCView.as_view(handle_request=self.handle_request)),
            path(f"{prefix}/health", PyRPCView.as_view()),
        ]) 