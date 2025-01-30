# PyRPC

![pre-alpha](https://img.shields.io/badge/status-pre--alpha-red)

A type-safe RPC framework for Python, inspired by tRPC.

## Features

- Full type safety from client to server
- Built on Pydantic
- Simple, declarative API definitions

## Example

```python
from pydantic import BaseModel
from pyrpc.typed_router import t

class AddInput(BaseModel):
    a: int
    b: int

class AddOutput(BaseModel):
    result: int

class CalculatorAPI:
    async def add(self, input: AddInput) -> AddOutput:
        return AddOutput(result=input.a + input.b)

router = t(CalculatorAPI)
```

Client:

```python
client = create_caller(router, "http://localhost:8000/api")
result = await client.add(AddInput(a=1, b=2))
print(result.result)  # 3
```
