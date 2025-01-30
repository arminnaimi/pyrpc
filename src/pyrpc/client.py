"""PyRPC Client Module

This module provides the client-side implementation for PyRPC, enabling type-safe
RPC calls to PyRPC servers. It includes client configuration, procedure calling,
and error handling.

Key Components:
    - PyRPCClient: Main client class for making RPC calls
    - ClientConfig: Configuration class for the client
    - TypedProcedure: Type-safe procedure caller
    - ProcedureCaller: Helper class for managing procedure calls

Example:
    ```python
    from pydantic import BaseModel
    from pyrpc import PyRPCClient, ClientConfig

    class UserInput(BaseModel):
        id: int

    class UserOutput(BaseModel):
        id: int
        name: str

    # Create a client
    client = PyRPCClient(
        ClientConfig(base_url="http://localhost:8000/trpc")
    )

    # Create a type-safe procedure
    users = client.caller("users")
    get_user = users.procedure("getUser", UserInput, UserOutput)

    # Make type-safe calls
    user = await get_user({"id": 1})  # Returns UserOutput
    print(user.name)  # IDE autocompletion works!
    ```
"""

from typing import Any, TypeVar, Generic, Type, Optional, Dict, Callable, Protocol, Union, get_type_hints
from pydantic import BaseModel
import httpx
import json
from dataclasses import dataclass
from .core import PyRPCError

Input = TypeVar("Input", bound=BaseModel)
Output = TypeVar("Output", bound=BaseModel)

@dataclass
class ClientConfig:
    """Configuration for the PyRPC client.
    
    Args:
        base_url (str): The base URL of the PyRPC server
        headers (Optional[dict[str, str]]): Optional HTTP headers to include in requests

    Example:
        ```python
        config = ClientConfig(
            base_url="http://localhost:8000/trpc",
            headers={"Authorization": "Bearer token"}
        )
        ```
    """
    base_url: str
    headers: Optional[dict[str, str]] = None

class ProcedureType(Protocol[Input, Output]):
    """Protocol for type-safe procedure definitions.
    
    This protocol defines the interface for procedure calls, enabling
    static type checking and IDE support.
    """
    def __call__(self, input: Input) -> Output: ...

class TypedProcedure(Generic[Input, Output]):
    """Type-safe procedure caller.
    
    This class provides a type-safe way to call RPC procedures, with full
    IDE support and runtime validation.

    Args:
        caller (ProcedureCaller): The procedure caller instance
        path (str): The procedure path
        input_type (Type[Input]): Input model type for validation
        output_type (Type[Output]): Output model type for validation
        is_mutation (bool): Whether this is a mutation procedure

    Example:
        ```python
        procedure = TypedProcedure(
            caller,
            "getUser",
            UserInput,
            UserOutput
        )
        result = await procedure({"id": 1})
        ```
    """
    def __init__(
        self,
        caller: "ProcedureCaller",
        path: str,
        input_type: Type[Input],
        output_type: Type[Output],
        is_mutation: bool = False
    ):
        self.caller = caller
        self.path = path
        self.input_type = input_type
        self.output_type = output_type
        self.is_mutation = is_mutation

    async def __call__(self, input_data: Union[Input, dict]) -> Output:
        """Call the procedure with type checking.
        
        Args:
            input_data (Union[Input, dict]): Input data, either as a model instance or dict

        Returns:
            Output: The validated output model instance

        Raises:
            PyRPCClientError: If the call fails
        """
        # Validate input
        if isinstance(input_data, dict):
            validated_input = self.input_type.model_validate(input_data)
        else:
            validated_input = input_data

        # Make the request
        result = await (
            self.caller.mutation(self.path, validated_input)
            if self.is_mutation
            else self.caller.query(self.path, validated_input)
        )

        # Validate and return output
        return self.output_type.model_validate(result)

class ProcedureCaller:
    """Helper class for managing procedure calls.
    
    This class manages procedure calls for a specific path prefix,
    providing type-safe procedure creation and caching.

    Example:
        ```python
        caller = ProcedureCaller(client, "users")
        get_user = caller.procedure("getUser", UserInput, UserOutput)
        ```
    """
    def __init__(self, client: "PyRPCClient", base_path: str):
        """Initialize a new procedure caller.
        
        Args:
            client (PyRPCClient): The PyRPC client instance
            base_path (str): The base path for all procedures
        """
        self.client = client
        self.base_path = base_path
        self._procedures: Dict[str, TypedProcedure] = {}

    def procedure(
        self,
        path: str,
        input_type: Type[Input],
        output_type: Type[Output],
        is_mutation: bool = False
    ) -> TypedProcedure[Input, Output]:
        """Create a type-safe procedure.
        
        Args:
            path (str): The procedure path
            input_type (Type[Input]): Input model type
            output_type (Type[Output]): Output model type
            is_mutation (bool): Whether this is a mutation procedure

        Returns:
            TypedProcedure: A type-safe procedure caller
        """
        if path not in self._procedures:
            self._procedures[path] = TypedProcedure(
                self,
                path,
                input_type,
                output_type,
                is_mutation
            )
        return self._procedures[path]

    async def query(self, procedure: str, input_data: BaseModel) -> Any:
        """Make a query request.
        
        Args:
            procedure (str): The procedure path
            input_data (BaseModel): The input data model

        Returns:
            Any: The raw response data
        """
        return await self._request("query", procedure, input_data)

    async def mutation(self, procedure: str, input_data: BaseModel) -> Any:
        """Make a mutation request.
        
        Args:
            procedure (str): The procedure path
            input_data (BaseModel): The input data model

        Returns:
            Any: The raw response data
        """
        return await self._request("mutation", procedure, input_data)

    async def _request(self, type_: str, procedure: str, input_data: BaseModel) -> Any:
        """Make a request to the PyRPC server.
        
        Args:
            type_ (str): The request type ("query" or "mutation")
            procedure (str): The procedure path
            input_data (BaseModel): The input data model

        Returns:
            Any: The response data

        Raises:
            PyRPCClientError: If the request fails
        """
        full_path = f"{self.base_path}.{procedure}"
        
        try:
            response = await self.client.client.post(
                f"/{type_}/{full_path}",
                json={"input": input_data.model_dump()}
            )
            response.raise_for_status()
            
            result = response.json()
            if "error" in result:
                raise PyRPCClientError(
                    result["error"].get("code", "UNKNOWN"),
                    result["error"].get("message", "Unknown error")
                )
                
            return result["result"]
            
        except httpx.HTTPError as e:
            raise PyRPCClientError("NETWORK_ERROR", str(e))

class PyRPCClient:
    """Main PyRPC client class.
    
    This class provides the main interface for making RPC calls to a PyRPC server.
    It manages the HTTP client and procedure callers.

    Example:
        ```python
        client = PyRPCClient(
            ClientConfig(base_url="http://localhost:8000/trpc")
        )
        users = client.caller("users")
        ```
    """
    def __init__(self, config: ClientConfig):
        """Initialize a new PyRPC client.
        
        Args:
            config (ClientConfig): The client configuration
        """
        self.config = config
        self.client = httpx.AsyncClient(
            base_url=config.base_url,
            headers=config.headers or {}
        )
        self._callers: Dict[str, ProcedureCaller] = {}
    
    def caller(self, path: str) -> ProcedureCaller:
        """Get or create a procedure caller for a path.
        
        Args:
            path (str): The base path for the caller

        Returns:
            ProcedureCaller: A procedure caller instance
        """
        if path not in self._callers:
            self._callers[path] = ProcedureCaller(self, path)
        return self._callers[path]

class PyRPCClientError(Exception):
    """Error class for PyRPC client errors.
    
    Args:
        code (str): The error code
        message (str): The error message

    Example:
        ```python
        raise PyRPCClientError("NOT_FOUND", "User not found")
        ```
    """
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")

# Example usage:
# from pydantic import BaseModel
# 
# class UserInput(BaseModel):
#     id: int
# 
# class UserOutput(BaseModel):
#     id: int
#     name: str
# 
# client = PyRPCClient(ClientConfig(base_url="http://localhost:8000/trpc"))
# users = client.caller("users")
# get_user = users.procedure("getUser", UserInput, UserOutput)
# 
# # Type-safe usage:
# user = await get_user(UserInput(id=1))  # Returns UserOutput
# # or
# user = await get_user({"id": 1})  # Also works and validates input 