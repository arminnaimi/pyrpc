from dataclasses import dataclass
from typing import Any, Callable, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


@dataclass
class PyRPCContext:
    """Base context class that can be extended with custom properties"""

    raw_request: Any = None
    user: Optional[Any] = None

    def set_user(self, user: Any) -> None:
        self.user = user


class MiddlewareFunction(BaseModel):
    """Type for middleware functions"""

    async def __call__(self, ctx: PyRPCContext, next: Callable[..., Any]) -> Any:
        return await next(ctx)


class MiddlewareBuilder:
    def __init__(self):
        self.middlewares: list[MiddlewareFunction] = []

    def use(self, middleware: MiddlewareFunction) -> None:
        """Add a middleware to the chain"""
        self.middlewares.append(middleware)

    async def handle(self, ctx: PyRPCContext, handler: Callable[..., Any]) -> Any:
        """Execute the middleware chain"""

        async def execute_middleware(index: int) -> Any:
            if index >= len(self.middlewares):
                return await handler(ctx)

            middleware = self.middlewares[index]
            return await middleware(ctx, lambda c: execute_middleware(index + 1))

        return await execute_middleware(0)
