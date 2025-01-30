"""PyRPC Core Module

This module implements the core functionality of PyRPC, providing a
type-safe RPC framework for Python applications. It includes the router implementation,
procedure definitions, and error handling mechanisms.

Key Components:
    - PyRPCRouter: The main router class for handling RPC procedures
    - ProcedureDef: Definition class for individual RPC procedures
    - ProcedureBuilder: Builder pattern implementation for creating procedures
    - PyRPCError: Base error class for RPC-specific exceptions

Example:
    ```python
    from pydantic import BaseModel
    from pyrpc import PyRPCRouter

    class UserInput(BaseModel):
        id: int

    class UserOutput(BaseModel):
        id: int
        name: str

    router = PyRPCRouter()

    @router.query("getUser")
    def get_user(input: UserInput) -> UserOutput:
        # Implementation
        return UserOutput(id=input.id, name="John Doe")
    ```
"""

import asyncio
from dataclasses import dataclass, field
from inspect import signature
from typing import Any, Callable, Generic, Optional, Self, Type, TypeVar, get_type_hints

from pydantic import BaseModel, ValidationError

from .context import MiddlewareBuilder, PyRPCContext

Input = TypeVar("Input", bound=BaseModel)
Output = TypeVar("Output", bound=BaseModel)


class PyRPCError(Exception):
    """Base error class for PyRPC errors.

    This exception class provides structured error handling for RPC operations,
    including error codes, status codes, and optional cause tracking.

    Args:
        code (str): A string identifier for the error type (e.g., "NOT_FOUND")
        message (str): Human-readable error description
        cause (Optional[Exception]): The underlying exception that caused this error
        status_code (Optional[int]): HTTP status code for the error

    Example:
        ```python
        raise PyRPCError(
            code="NOT_FOUND",
            message="User with ID 123 not found"
        )
        ```
    """

    # Default status code mapping
    STATUS_CODES = {
        "VALIDATION_ERROR": 400,
        "BAD_REQUEST": 400,
        "UNAUTHORIZED": 401,
        "FORBIDDEN": 403,
        "NOT_FOUND": 404,
        "METHOD_NOT_ALLOWED": 405,
        "CONFLICT": 409,
        "INTERNAL_SERVER_ERROR": 500,
        "NOT_IMPLEMENTED": 501,
    }

    def __init__(
        self,
        code: str,
        message: str,
        cause: Optional[Exception] = None,
        status_code: Optional[int] = None,
    ):
        self.code = code
        self.message = message
        self.cause = cause
        # Ensure status code is set from parameter or mapping
        if status_code is not None:
            self.status_code = status_code
        else:
            self.status_code = self.STATUS_CODES.get(code, 500)
        print(f"PyRPCError initialized: code={code}, status_code={self.status_code}")
        super().__init__(message)


@dataclass
class ProcedureDef(Generic[Input, Output]):
    """Definition of a PyRPC procedure.

    This class holds the complete definition of an RPC procedure, including its
    resolver function, input/output models, and metadata.

    Args:
        resolver (Callable): The function that implements the procedure logic
        input_model (Type[Input]): Pydantic model class for procedure input validation
        output_model (Type[Output]): Pydantic model class for
        procedure output validation is_mutation (bool): Whether this
        procedure modifies state (default: False)
        meta (dict): Additional metadata for the procedure
        takes_context (bool): Whether the resolver accepts a context parameter

    Example:
        ```python
        def get_user(input: UserInput) -> UserOutput:
            return UserOutput(id=input.id, name="John")

        procedure = ProcedureDef(
            resolver=get_user,
            input_model=UserInput,
            output_model=UserOutput
        )
        ```
    """

    resolver: Callable[..., Output]  # Use ... to accept variable arguments
    input_model: Type[Input]
    output_model: Type[Output]
    is_mutation: bool = False
    meta: dict[str, Any] = field(default_factory=dict)
    takes_context: bool = False


class ProcedureBuilder(Generic[Input, Output]):
    """Builder for creating PyRPC procedures"""

    def __init__(
        self,
        router: "PyRPCRouter",
        procedure_type: str = "query",
        input_model: Optional[Type[Input]] = None,
        output_model: Optional[Type[Output]] = None,
    ):
        self.router = router
        self.procedure_type = procedure_type
        self._input_model = input_model
        self._output_model = output_model
        self._resolver: Optional[
            Callable[[Input, PyRPCContext], Output] | Callable[[Input], Output]
        ] = None
        self._meta: dict[str, Any] = {}
        self._current_path: Optional[str] = None

    def _path(self, path: str) -> Self:
        """Set the path for the procedure"""
        self._current_path = path
        return self

    def input(self, model: Type[Input]) -> Self:
        """Set the input model for the procedure"""
        self._input_model = model
        return self

    def output(self, model: Type[Output]) -> Self:
        """Set the output model for the procedure"""
        self._output_model = model
        return self

    def resolver(self, fn: Callable[[Input, PyRPCContext], Output]) -> Self:
        """Set the resolver function for the procedure"""
        self._resolver = fn
        return self

    def meta(self, meta_data: dict[str, Any]) -> Self:
        """Add metadata to the procedure"""
        self._meta.update(meta_data)
        return self

    def __call__(
        self, fn: Callable[[Input], Output] | Callable[[Input, PyRPCContext], Output]
    ) -> Callable:
        """Support for decorator pattern"""
        # Get type hints from the function
        hints = get_type_hints(fn)
        sig = signature(fn)

        # Check if function takes context
        takes_context = len(sig.parameters) > 1

        # First argument should be the input type
        input_type = next(iter(hints.values()))
        # Return type is the output type
        output_type = hints.get("return")

        if not input_type or not output_type:
            raise PyRPCError(
                "VALIDATION", "Function must have input and output type hints"
            )

        # Set the types and resolver
        self._input_model = input_type
        self._output_model = output_type
        self._resolver = fn

        # Build and register the procedure
        procedure = ProcedureDef(
            resolver=fn,
            input_model=input_type,
            output_model=output_type,
            is_mutation=self.procedure_type == "mutation",
            meta=self._meta,
            takes_context=takes_context,
        )
        procedure._current_path = self._current_path  # type: ignore
        self.router.procedure(procedure)

        return fn

    def build(self) -> ProcedureDef[Input, Output]:
        """Build the procedure definition"""
        if not self._input_model:
            raise PyRPCError("VALIDATION", "Missing input model")
        if not self._output_model:
            raise PyRPCError("VALIDATION", "Missing output model")
        if not self._resolver:
            raise PyRPCError("VALIDATION", "Missing resolver")

        return ProcedureDef(
            resolver=self._resolver,
            input_model=self._input_model,
            output_model=self._output_model,
            is_mutation=self.procedure_type == "mutation",
            meta=self._meta,
        )


class PyRPCRouter:
    """Main PyRPC router class for handling RPC procedures.

    This class manages the registration and execution of RPC procedures. It supports
    queries, mutations, middleware, and nested routers.

    Example:
        ```python
        router = PyRPCRouter()

        # Define a query
        @router.query("getUser")
        def get_user(input: UserInput) -> UserOutput:
            return UserOutput(id=input.id, name="John")

        # Define a mutation
        @router.mutation("createUser")
        def create_user(input: CreateUserInput) -> UserOutput:
            # Implementation
            return UserOutput(id=1, name=input.name)

        # Merge routers
        users_router = PyRPCRouter()
        router.merge("users", users_router)
        ```
    """

    def __init__(self):
        """Initialize a new PyRPC router."""
        self.procedures: dict[str, ProcedureDef] = {}
        self.routers: dict[str, "PyRPCRouter"] = {}
        self.middleware = MiddlewareBuilder()

    def query(self, path: str) -> ProcedureBuilder:
        """Create a query procedure.

        Args:
            path (str): The path identifier for the procedure

        Returns:
            ProcedureBuilder: A builder instance for creating the query

        Example:
            ```python
            @router.query("getUser")
            def get_user(input: UserInput) -> UserOutput:
                return UserOutput(id=input.id, name="John")
            ```
        """
        builder = ProcedureBuilder(self, procedure_type="query")
        builder._path(path)
        return builder

    def mutation(self, path: str) -> ProcedureBuilder:
        """Create a mutation procedure.

        Args:
            path (str): The path identifier for the procedure

        Returns:
            ProcedureBuilder: A builder instance for creating the mutation

        Example:
            ```python
            @router.mutation("createUser")
            def create_user(input: CreateUserInput) -> UserOutput:
                return UserOutput(id=1, name=input.name)
            ```
        """
        builder = ProcedureBuilder(self, procedure_type="mutation")
        builder._path(path)
        return builder

    def merge(self, prefix: str, router: "PyRPCRouter"):
        """Merge another router under a prefix.

        Args:
            prefix (str): The prefix to mount the router under
            router (PyRPCRouter): The router to merge

        Example:
            ```python
            users_router = PyRPCRouter()
            posts_router = PyRPCRouter()

            main_router = PyRPCRouter()
            main_router.merge("users", users_router)
            main_router.merge("posts", posts_router)
            ```
        """
        self.routers[prefix] = router

    def procedure(self, defs: ProcedureDef) -> Self:
        """Add a procedure to the router"""
        if not hasattr(defs, "_current_path"):
            raise PyRPCError("CONFIG", "Missing procedure path")

        self.procedures[defs._current_path] = defs  # type: ignore
        return self

    async def _find_procedure(self, path: str) -> ProcedureDef:
        """Find a procedure by path"""
        procedure = self.procedures.get(path)
        if not procedure:
            for prefix, router in self.routers.items():
                if path.startswith(prefix + "."):
                    return await router._find_procedure(path[len(prefix) + 1 :])
            raise PyRPCError(
                "NOT_FOUND", f"Procedure {path} not found", status_code=404
            )
        return procedure

    async def _execute_procedure(
        self, procedure: ProcedureDef, validated_input: Any, ctx: PyRPCContext
    ) -> Any:
        """Execute a procedure with validated input"""
        try:
            if procedure.takes_context:
                result = procedure.resolver(validated_input, ctx)
            else:
                result = procedure.resolver(validated_input)
            if asyncio.iscoroutine(result):
                result = await result
            return procedure.output_model.model_validate(result)
        except PyRPCError as e:
            if not hasattr(e, "status_code") or e.status_code is None:
                e.status_code = PyRPCError.STATUS_CODES.get(e.code, 500)
            raise e
        except Exception as e:
            raise PyRPCError(
                "INTERNAL_SERVER_ERROR", str(e), cause=e, status_code=500
            ) from e

    async def handle(
        self, path: str, input_data: Any, context: Optional[PyRPCContext] = None
    ) -> Any:
        """Handle an incoming request"""
        if context is None:
            context = PyRPCContext()

        try:
            procedure = await self._find_procedure(path)
            validated_input = procedure.input_model.model_validate(input_data)
            return await self.middleware.handle(
                context,
                lambda ctx: self._execute_procedure(procedure, validated_input, ctx),
            )
        except ValidationError as e:
            raise PyRPCError("VALIDATION_ERROR", str(e), status_code=400) from e
        except PyRPCError as e:
            if not hasattr(e, "status_code") or e.status_code is None:
                e.status_code = PyRPCError.STATUS_CODES.get(e.code, 500)
            raise e
        except Exception as e:
            raise PyRPCError(
                "INTERNAL_SERVER_ERROR", str(e), cause=e, status_code=500
            ) from e
