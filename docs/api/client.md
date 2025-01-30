# Client API Reference

The PyRPC client provides a type-safe way to consume PyRPC APIs. It includes automatic input/output validation and full IDE support.

## PyRPCClient

The main client class for making RPC calls.

```python
from pyrpc import PyRPCClient, ClientConfig

client = PyRPCClient(
    ClientConfig(base_url="http://localhost:8000/pyrpc")
)
```

### Methods

#### caller

Get or create a procedure caller for a path.

```python
def caller(path: str) -> ProcedureCaller
```

**Parameters:**
- `path` (str): The base path for the caller

**Returns:**
- `ProcedureCaller`: A procedure caller instance

**Example:**
```python
users = client.caller("users")
posts = client.caller("posts")
```

## ClientConfig

Configuration class for the PyRPC client.

```python
@dataclass
class ClientConfig:
    base_url: str
    headers: Optional[dict[str, str]] = None
```

**Attributes:**
- `base_url` (str): The base URL of the PyRPC server
- `headers` (Optional[dict[str, str]]): Optional HTTP headers to include in requests

**Example:**
```python
config = ClientConfig(
    base_url="http://localhost:8000/pyrpc",
    headers={
        "Authorization": "Bearer token",
        "X-Custom-Header": "value"
    }
)
```

## ProcedureCaller

Helper class for managing procedure calls for a specific path prefix.

### Methods

#### procedure

Create a type-safe procedure.

```python
def procedure(
    path: str,
    input_type: Type[Input],
    output_type: Type[Output],
    is_mutation: bool = False
) -> TypedProcedure[Input, Output]
```

**Parameters:**
- `path` (str): The procedure path
- `input_type` (Type[Input]): Input model type
- `output_type` (Type[Output]): Output model type
- `is_mutation` (bool): Whether this is a mutation procedure

**Returns:**
- `TypedProcedure`: A type-safe procedure caller

**Example:**
```python
from pydantic import BaseModel

class UserInput(BaseModel):
    id: int

class UserOutput(BaseModel):
    id: int
    name: str

users = client.caller("users")
get_user = users.procedure("getUser", UserInput, UserOutput)
create_user = users.procedure(
    "createUser",
    CreateUserInput,
    UserOutput,
    is_mutation=True
)
```

## TypedProcedure

Type-safe procedure caller that provides input validation and IDE support.

### Methods

#### __call__

Call the procedure with type checking.

```python
async def __call__(input_data: Union[Input, dict]) -> Output
```

**Parameters:**
- `input_data` (Union[Input, dict]): Input data, either as a model instance or dict

**Returns:**
- `Output`: The validated output model instance

**Raises:**
- `PyRPCClientError`: If the call fails

**Example:**
```python
# Using with dict input
user = await get_user({"id": 1})
print(user.name)  # IDE autocompletion works!

# Using with model instance
input_model = UserInput(id=1)
user = await get_user(input_model)
```

## Error Handling

The client includes built-in error handling through the `PyRPCClientError` class:

```python
class PyRPCClientError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
```

**Example:**
```python
try:
    user = await get_user({"id": 999})
except PyRPCClientError as e:
    if e.code == "NOT_FOUND":
        print(f"User not found: {e.message}")
    else:
        print(f"Error: {e.code} - {e.message}")
```

## Complete Example

Here's a complete example showing various client features:

```python
from pyrpc import PyRPCClient, ClientConfig
from pydantic import BaseModel

# Define models
class UserInput(BaseModel):
    id: int

class CreateUserInput(BaseModel):
    name: str
    email: str

class UserOutput(BaseModel):
    id: int
    name: str
    email: str

# Create client
client = PyRPCClient(
    ClientConfig(
        base_url="http://localhost:8000/pyrpc",
        headers={"Authorization": "Bearer token"}
    )
)

# Create procedure callers
users = client.caller("users")
get_user = users.procedure("getUser", UserInput, UserOutput)
create_user = users.procedure(
    "createUser",
    CreateUserInput,
    UserOutput,
    is_mutation=True
)

# Use procedures
async def main():
    try:
        # Create a user
        new_user = await create_user({
            "name": "John Doe",
            "email": "john@example.com"
        })
        print(f"Created user: {new_user.name}")

        # Get the user
        user = await get_user({"id": new_user.id})
        print(f"Found user: {user.email}")

    except PyRPCClientError as e:
        print(f"Error: {e.code} - {e.message}")
``` 