# Calculator Example

This example demonstrates how to use PyRPC with different web frameworks (FastAPI, Flask, and Django) to create a simple calculator service with type-safe RPC calls.

## Features

- Basic arithmetic operations (add, subtract, multiply, divide)
- Calculation history tracking
- Type-safe inputs and outputs using Pydantic models
- Framework integrations:
  - FastAPI integration (`server.py`)
  - Flask integration (`server_flask.py`)
  - Django integration (`server_django.py`)
- Async client implementation
- Validation middleware

## Project Structure

```
calculator/
├── models.py           # Pydantic models for type safety
├── server.py          # FastAPI server implementation
├── server_flask.py    # Flask server implementation
├── server_django.py   # Django server implementation
├── client.py          # PyRPC client implementation
└── README.md          # This file
```

## Running the Examples

1. Make sure you have the required dependencies:

```bash
# For FastAPI example
pip install pyrpc[fastapi] uvicorn

# For Flask example
pip install pyrpc[flask]

# For Django example
pip install pyrpc[django] uvicorn

# For all examples
pip install pyrpc[all] uvicorn
```

2. Start one of the servers:

```bash
# FastAPI server
python server.py

# Flask server
python server_flask.py

# Django server
python server_django.py
```

3. In another terminal, run the client:

```bash
python client.py
```

## API Endpoints

All three implementations provide the same RPC endpoints:

- `add`: Add two numbers
- `subtract`: Subtract two numbers
- `multiply`: Multiply two numbers
- `divide`: Divide two numbers
- `history`: Get calculation history

## Framework-Specific Features

### FastAPI Version

- Automatic OpenAPI documentation at `/docs`
- Built-in CORS support
- Native async support

### Flask Version

- Lightweight and simple
- Easy to integrate with existing Flask apps
- Synchronous with async wrapper

### Django Version

- Full Django integration
- ASGI support
- Works with Django's URL routing

## Type Safety

All implementations demonstrate PyRPC's type safety features:

- Input validation using Pydantic models
- Type-safe procedure calls
- Automatic error handling
- IDE autocompletion support

## Error Handling

The example includes comprehensive error handling:

- Division by zero protection
- Input validation
- Type validation
- Middleware error handling

## Example Usage

The example includes a full-featured client that demonstrates all calculator operations. Here's how to use it:

### Running the Client

```bash
python client.py
```

Expected output:
```
5 + 3 = 8
10 - 4 = 6
6 * 7 = 42
15 / 3 = 5
Division by zero error: Cannot divide by zero

Last 5 calculations:
5 add 3 = 8
10 subtract 4 = 6
6 multiply 7 = 42
15 divide 3 = 5
```

### Client Code Explanation

The client demonstrates several key features of PyRPC:

1. **Client Setup**:
```python
client = PyRPCClient(
    ClientConfig(base_url="http://localhost:8000/api")
)
```

2. **Type-Safe Procedure Creation**:
```python
calc = client.caller("calculator")
add = calc.procedure("add", CalculationInput, CalculationOutput)
subtract = calc.procedure("subtract", CalculationInput, CalculationOutput)
```

3. **Making Calls**:
```python
# Simple calculation
result = await add({"a": 5, "b": 3})
print(f"5 + 3 = {result.result}")

# With error handling
try:
    await divide({"a": 1, "b": 0})
except PyRPCError as e:
    print(f"Error: {e.code} - {e.message}")
```

4. **Working with Complex Responses**:
```python
# Get calculation history
history_result = await history({"limit": 5})
for entry in history_result.entries:
    print(f"{entry.a} {entry.operation} {entry.b} = {entry.result}")
```

### Key Features Demonstrated

- Type safety for inputs and outputs
- Async/await support
- Error handling with PyRPCError
- Complex data structures (history entries)
- Framework-agnostic client (works with all server implementations)

## Framework Comparison

Each framework has its strengths:

- **FastAPI**: Best for new projects needing modern features and automatic docs
- **Flask**: Best for simple projects or adding to existing Flask apps
- **Django**: Best for complex projects needing Django's ecosystem

The PyRPC code remains the same across all frameworks, demonstrating its framework-agnostic design.

## CURL Examples

All examples work with any of the server implementations (FastAPI, Flask, or Django). Just make sure to use the correct port if you changed it.

### Add Numbers

```bash
curl -X POST http://localhost:8000/api/query/add \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "a": 5,
      "b": 3
    }
  }'

# Expected Response:
# {
#   "success": true,
#   "result": {
#     "result": 8,
#     "operation": "add"
#   }
# }
```

### Subtract Numbers

```bash
curl -X POST http://localhost:8000/api/query/subtract \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "a": 10,
      "b": 4
    }
  }'

# Expected Response:
# {
#   "success": true,
#   "result": {
#     "result": 6,
#     "operation": "subtract"
#   }
# }
```

### Multiply Numbers

```bash
curl -X POST http://localhost:8000/api/query/multiply \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "a": 6,
      "b": 7
    }
  }'

# Expected Response:
# {
#   "success": true,
#   "result": {
#     "result": 42,
#     "operation": "multiply"
#   }
# }
```

### Divide Numbers

```bash
curl -X POST http://localhost:8000/api/query/divide \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "a": 15,
      "b": 3
    }
  }'

# Expected Response:
# {
#   "success": true,
#   "result": {
#     "result": 5,
#     "operation": "divide"
#   }
# }

# Division by zero error:
curl -X POST http://localhost:8000/api/query/divide \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "a": 1,
      "b": 0
    }
  }'

# Expected Error Response:
# {
#   "success": false,
#   "error": {
#     "code": "INVALID_INPUT",
#     "message": "Cannot divide by zero"
#   }
# }
```

### Get Calculation History

```bash
curl -X POST http://localhost:8000/api/query/history \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "limit": 5
    }
  }'

# Expected Response:
# {
#   "success": true,
#   "result": {
#     "entries": [
#       {
#         "operation": "add",
#         "a": 5,
#         "b": 3,
#         "result": 8
#       },
#       {
#         "operation": "multiply",
#         "a": 6,
#         "b": 7,
#         "result": 42
#       }
#       // ... more entries
#     ]
#   }
# }
```

### Error Examples

1. Invalid Input Type:

```bash
curl -X POST http://localhost:8000/api/query/add \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "a": "not a number",
      "b": 3
    }
  }'

# Expected Response:
# {
#   "success": false,
#   "error": {
#     "code": "VALIDATION_ERROR",
#     "message": "Input validation failed..."
#   }
# }
```

2. Invalid Content Type:

```bash
curl -X POST http://localhost:8000/api/query/add \
  -H "Content-Type: text/plain" \
  -d "not json"

# Expected Response:
# {
#   "success": false,
#   "error": {
#     "code": "UNSUPPORTED_MEDIA_TYPE",
#     "message": "Only application/json is supported"
#   }
# }
```
