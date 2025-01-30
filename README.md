# PyRPC

A modern, type-safe RPC framework for Python. PyRPC brings end-to-end type safety to your Python APIs, with built-in support for FastAPI, Flask, and Django.

## Features

- 🔒 End-to-end type safety with Pydantic
- 🚀 Framework agnostic (FastAPI, Flask, Django)
- 🔍 Runtime validation and error handling
- 🛠 Middleware support with async-first design
- 🌐 Clean, intuitive API design
- 📦 Modern Python packaging
- 🔧 Easy to extend and customize

## Installation

```bash
# Basic installation
pip install pyrpc

# With FastAPI support
pip install pyrpc[fastapi]

# With Flask support
pip install pyrpc[flask]

# With Django support
pip install pyrpc[django]

# With all framework support
pip install pyrpc[all]
```

## Quick Start

```python
from pydantic import BaseModel
from pyrpc import PyRPCRouter, PyRPCClient, ClientConfig

# Define your models with full type safety
class HelloInput(BaseModel):
    name: str

class HelloOutput(BaseModel):
    message: str

# Create a router
router = PyRPCRouter()

@router.query("hello")
def hello(input: HelloInput) -> HelloOutput:
    return HelloOutput(message=f"Hello {input.name}!")

# FastAPI example
from fastapi import FastAPI
from pyrpc.integrations import PyRPCFastAPI

app = FastAPI()
trpc = PyRPCFastAPI(router)
trpc.mount(app)

# Type-safe client usage
client = PyRPCClient(ClientConfig(base_url="http://localhost:8000/trpc"))
caller = client.caller("hello")
get_hello = caller.procedure("hello", HelloInput, HelloOutput)

# Full type safety and autocompletion
result = await get_hello({"name": "World"})
print(result.message)  # Hello World!
```

## Framework Integration

### FastAPI

```python
from fastapi import FastAPI
from pyrpc.integrations import PyRPCFastAPI

app = FastAPI()
trpc = PyRPCFastAPI(router)
trpc.mount(app)
```

### Flask

```python
from flask import Flask
from pyrpc.integrations import PyRPCFlask

app = Flask(__name__)
trpc = PyRPCFlask(router)
trpc.mount(app)
```

### Django

```python
# urls.py
from django.urls import path
from pyrpc.integrations import PyRPCDjango

urlpatterns = []
trpc = PyRPCDjango(router)
trpc.mount(urlpatterns)
```

## Advanced Features

### Middleware

```python
from pyrpc import PyRPCContext, MiddlewareFunction

class AuthMiddleware(MiddlewareFunction):
    async def __call__(self, ctx: PyRPCContext, next):
        # Add auth logic here
        ctx.user = get_user_from_request(ctx.raw_request)
        return await next(ctx)

router.middleware.use(AuthMiddleware())
```

### Nested Routers

```python
# Create feature-specific routers
users = PyRPCRouter()
posts = PyRPCRouter()

@users.query("list")
def list_users(input: ListUsersInput) -> list[UserOutput]:
    return get_users(limit=input.limit)

@posts.mutation("create")
def create_post(input: CreatePostInput) -> PostOutput:
    return create_new_post(input)

# Merge routers with prefixes
router.merge("users", users)
router.merge("posts", posts)
```

### Error Handling

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

### Type-safe Client Usage

```python
# Create type-safe procedures
users = client.caller("users")
list_users = users.procedure("list", ListUsersInput, list[UserOutput])
create_post = posts.procedure("create", CreatePostInput, PostOutput, is_mutation=True)

# Use with full type safety
users = await list_users({"limit": 10})
for user in users:
    print(user.name)  # IDE autocompletion works!

new_post = await create_post(CreatePostInput(
    title="Hello",
    content="World"
))
print(new_post.id)  # Type-safe access to fields
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT
