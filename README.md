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
pyrpc = PyRPCFastAPI(router)
pyrpc.mount(app)

# Type-safe client usage
client = PyRPCClient(ClientConfig(base_url="http://localhost:8000/api"))
caller = client.caller("hello")
get_hello = caller.procedure("hello", HelloInput, HelloOutput)

# Full type safety and autocompletion
result = await get_hello({"name": "World"})
print(result.message)  # Hello World!
```