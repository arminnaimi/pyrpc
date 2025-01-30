# Quick Start Guide

This guide will help you get started with PyRPC quickly. We'll create a simple API with type-safe endpoints and a client to consume them.

## Installation

```bash
# Basic installation
pip install pyrpc

# With FastAPI support (recommended for this guide)
pip install pyrpc[fastapi]
```

## Creating Your First API

Let's create a simple API for managing users:

```python
from pydantic import BaseModel
from fastapi import FastAPI
from pyrpc import PyRPCRouter, PyRPCFastAPI

# Define your models with full type safety
class User(BaseModel):
    id: int
    name: str
    email: str

class CreateUserInput(BaseModel):
    name: str
    email: str

class GetUserInput(BaseModel):
    id: int

# Create a router
router = PyRPCRouter()

# Define your procedures
@router.query("getUser")
def get_user(input: GetUserInput) -> User:
    # In a real app, you'd fetch from a database
    return User(
        id=input.id,
        name="John Doe",
        email="john@example.com"
    )

@router.mutation("createUser")
def create_user(input: CreateUserInput) -> User:
    # In a real app, you'd save to a database
    return User(
        id=1,
        name=input.name,
        email=input.email
    )

# Create FastAPI app and mount PyRPC
app = FastAPI()
pyrpc = PyRPCFastAPI(router)
pyrpc.mount(app)
```

## Using the Client

Now let's create a client to consume our API:

```python
from pyrpc import PyRPCClient, ClientConfig

# Create a client
client = PyRPCClient(
    ClientConfig(base_url="http://localhost:8000/api")
)

# Create type-safe procedures
users = client.caller("users")
get_user = users.procedure("getUser", GetUserInput, User)
create_user = users.procedure("createUser", CreateUserInput, User, is_mutation=True)

# Use the procedures with full type safety
async def main():
    # Create a user
    new_user = await create_user({
        "name": "Jane Doe",
        "email": "jane@example.com"
    })
    print(new_user.name)  # IDE autocompletion works!

    # Get a user
    user = await get_user({"id": 1})
    print(user.email)  # Type-safe access to fields
```

## Running the API

Save the API code in `main.py` and run it with uvicorn:

```bash
uvicorn main:app --reload
```

Your API will be available at `http://localhost:8000/pyrpc`, and you'll get:
- Automatic OpenAPI documentation at `/docs`
- Type-safe endpoints at `/pyrpc`
- Runtime validation of all inputs and outputs

## Next Steps

- Learn about [Basic Concepts](concepts.md)
- Explore [Middleware](../api/middleware.md) for authentication and logging
- See more [Examples](../examples/basic.md)
- Check out framework-specific guides:
  - [FastAPI Integration](fastapi.md)
  - [Flask Integration](flask.md)
  - [Django Integration](django.md) 