# Router API Reference

The `PyRPCRouter` is the core class for defining your RPC procedures. It provides methods for registering queries and mutations, handling requests, and managing middleware.

## PyRPCRouter

```python
from pyrpc import PyRPCRouter

router = PyRPCRouter()
```

### Methods

#### query

Register a query procedure (read-only operations).

```python
@router.query(path: str) -> ProcedureBuilder
```

**Parameters:**
- `path` (str): The path identifier for the procedure

**Returns:**
- `ProcedureBuilder`: A builder instance for creating the query

**Example:**
```python
from pydantic import BaseModel

class UserInput(BaseModel):
    id: int

class UserOutput(BaseModel):
    id: int
    name: str

@router.query("getUser")
def get_user(input: UserInput) -> UserOutput:
    return UserOutput(id=input.id, name="John Doe")
```

#### mutation

Register a mutation procedure (write operations).

```python
@router.mutation(path: str) -> ProcedureBuilder
```

**Parameters:**
- `path` (str): The path identifier for the procedure

**Returns:**
- `ProcedureBuilder`: A builder instance for creating the mutation

**Example:**
```python
@router.mutation("createUser")
def create_user(input: CreateUserInput) -> UserOutput:
    return UserOutput(id=1, name=input.name)
```

#### merge

Merge another router under a prefix for nested routing.

```python
def merge(prefix: str, router: PyRPCRouter) -> None
```

**Parameters:**
- `prefix` (str): The prefix to mount the router under
- `router` (PyRPCRouter): The router to merge

**Example:**
```python
# Create feature-specific routers
users = PyRPCRouter()
posts = PyRPCRouter()

@users.query("list")
def list_users() -> list[UserOutput]:
    return [UserOutput(id=1, name="John")]

@posts.mutation("create")
def create_post(input: CreatePostInput) -> PostOutput:
    return PostOutput(id=1, title=input.title)

# Merge routers with prefixes
main_router = PyRPCRouter()
main_router.merge("users", users)
main_router.merge("posts", posts)
```

### Middleware Support

The router includes built-in middleware support through the `middleware` property:

```python
from pyrpc import PyRPCContext, MiddlewareFunction

class AuthMiddleware(MiddlewareFunction):
    async def __call__(self, ctx: PyRPCContext, next):
        # Add auth logic here
        ctx.user = get_user_from_request(ctx.raw_request)
        return await next(ctx)

router.middleware.use(AuthMiddleware())
```

See [Middleware](middleware.md) for more details.

### Error Handling

The router automatically handles errors and converts them to appropriate responses:

```python
from pyrpc import PyRPCError

@router.query("user")
def get_user(input: GetUserInput) -> UserOutput:
    user = find_user(input.id)
    if not user:
        raise PyRPCError(
            code="NOT_FOUND",
            message=f"User {input.id} not found"
        )
    return UserOutput.from_orm(user)
```

See [Error Handling](errors.md) for more details.

## ProcedureDef

The `ProcedureDef` class represents a procedure definition. It's usually created automatically by the router decorators but can be created manually if needed.

```python
@dataclass
class ProcedureDef(Generic[Input, Output]):
    resolver: Callable[[Input, PyRPCContext], Output] | Callable[[Input], Output]
    input_model: Type[Input]
    output_model: Type[Output]
    is_mutation: bool = False
    meta: dict[str, Any] = None
    takes_context: bool = False
```

**Attributes:**
- `resolver`: The function that implements the procedure logic
- `input_model`: Pydantic model class for input validation
- `output_model`: Pydantic model class for output validation
- `is_mutation`: Whether this procedure modifies state
- `meta`: Additional metadata for the procedure
- `takes_context`: Whether the resolver accepts a context parameter

## ProcedureBuilder

The `ProcedureBuilder` class is used internally by the router decorators to build procedure definitions. It provides a fluent API for creating procedures:

```python
# Manual procedure creation (usually not needed)
builder = ProcedureBuilder(router, "query")
procedure = (
    builder
    .input(UserInput)
    .output(UserOutput)
    .resolver(get_user)
    .meta({"description": "Get a user by ID"})
    .build()
)
```

See [Procedures](procedures.md) for more details on procedure configuration. 