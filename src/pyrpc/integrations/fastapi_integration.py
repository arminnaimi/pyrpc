"""FastAPI integration for PyRPC"""
from typing import Any, Optional
from fastapi import FastAPI, APIRouter, Response
from ..core import PyRPCRouter, PyRPCError
from ..context import PyRPCContext
from .base import BasePyRPCIntegration
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json
from starlette.requests import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

class PyRPCFastAPI(BasePyRPCIntegration):
    """FastAPI integration for PyRPC"""
    def __init__(self, router: PyRPCRouter, prefix: str = "/api", cors_config: Optional[dict] = None):
        super().__init__(router)
        self.api_router = APIRouter()
        self.prefix = prefix
        self.cors_config = cors_config

    async def handle_request(self, path: str, input_data: Any, context: Optional[PyRPCContext] = None):
        """Handle FastAPI request"""
        return await self.router.handle(path, input_data, context)

    def mount(self, app: FastAPI):
        """Mount PyRPC routes on FastAPI app"""
        from fastapi.exceptions import RequestValidationError
        from pydantic import ValidationError
        from fastapi.middleware.cors import CORSMiddleware
        from starlette.requests import Request
        from starlette.responses import Response
        from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
        from starlette.types import ASGIApp

        # Add error handling middleware first
        class PyRPCErrorMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
                try:
                    response = await call_next(request)
                    return response
                except PyRPCError as e:
                    status_code = getattr(e, 'status_code', None)
                    if status_code is None:
                        status_code = PyRPCError.STATUS_CODES.get(e.code, 500)
                    
                    return JSONResponse(
                        status_code=status_code,
                        content={
                            "error": {"code": e.code, "message": str(e)},
                            "success": False
                        }
                    )
                except Exception as e:
                    return JSONResponse(
                        status_code=500,
                        content={
                            "error": {"code": "INTERNAL_SERVER_ERROR", "message": str(e)},
                            "success": False
                        }
                    )

        app.add_middleware(PyRPCErrorMiddleware)

        # Setup CORS if configured
        if self.cors_config:
            app.add_middleware(
                CORSMiddleware,
                allow_origins=self.cors_config.get("allow_origins", ["*"]),
                allow_credentials=self.cors_config.get("allow_credentials", True),
                allow_methods=self.cors_config.get("allow_methods", ["*"]),
                allow_headers=self.cors_config.get("allow_headers", ["*"]),
            )

        @self.api_router.post("/query/{path:path}")
        async def handle_query(path: str, request: Request):
            # Check content type first
            if request.headers.get("content-type") != "application/json":
                return JSONResponse(
                    status_code=415,
                    content={
                        "error": {"code": "UNSUPPORTED_MEDIA_TYPE", "message": "Only application/json is supported"},
                        "success": False
                    }
                )

            try:
                request_data = await request.json()
                result = await self.handle_request(path, request_data.get("input"))
                return JSONResponse(
                    status_code=200,
                    content={
                        "result": result.model_dump(),
                        "success": True
                    }
                )
            except json.JSONDecodeError:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": {"code": "INVALID_JSON", "message": "Invalid JSON payload"},
                        "success": False
                    }
                )

        @self.api_router.post("/mutation/{path:path}")
        async def handle_mutation(path: str, request_data: dict, response: Response):
            try:
                result = await self.handle_request(path, request_data.get("input"))
                return JSONResponse(
                    status_code=200,
                    content={
                        "result": result.model_dump(),
                        "success": True
                    }
                )
            except PyRPCError as e:
                # Debug info
                print(f"FastAPI caught error: code={e.code}, status_code={getattr(e, 'status_code', None)}")
                print(f"Error attributes: {vars(e)}")
                
                # Get the status code from the error
                status_code = e.status_code
                if status_code is None:
                    status_code = PyRPCError.STATUS_CODES.get(e.code, 500)
                    print(f"Using fallback status code: {status_code}")
                else:
                    print(f"Using error status code: {status_code}")
                
                return JSONResponse(
                    status_code=status_code,
                    content={
                        "error": {"code": e.code, "message": str(e)},
                        "success": False
                    }
                )
            except Exception as e:
                return JSONResponse(
                    status_code=500,
                    content={
                        "error": {"code": "INTERNAL_SERVER_ERROR", "message": str(e)},
                        "success": False
                    }
                )

        @self.api_router.get("/health")
        async def health_check():
            return {"status": "healthy"}

        # Handle FastAPI validation errors
        @app.exception_handler(RequestValidationError)
        async def validation_exception_handler(request: Request, exc: RequestValidationError):
            return JSONResponse(
                status_code=400,
                content={
                    "error": {"code": "VALIDATION_ERROR", "message": str(exc)},
                    "success": False
                }
            )

        # Handle malformed JSON
        @app.exception_handler(ValidationError)
        async def pydantic_validation_handler(request: Request, exc: ValidationError):
            return JSONResponse(
                status_code=400,
                content={
                    "error": {"code": "VALIDATION_ERROR", "message": str(exc)},
                    "success": False
                }
            )

        app.include_router(self.api_router, prefix=self.prefix)

# Example usage:
# app = FastAPI()
# router = PyRPCRouter()
# pyrpc = PyRPCFastAPI(router)
# pyrpc.mount(app) 