# Calculator Example

This example demonstrates how to use PyRPC to create a simple calculator service with type-safe RPC calls.

## Features

- Basic arithmetic operations (add, subtract, multiply, divide)
- Calculation history tracking
- Type-safe inputs and outputs using Pydantic models
- FastAPI integration
- Async client implementation

## Project Structure

```
calculator/
├── models.py      # Pydantic models for type safety
├── server.py      # FastAPI server with PyRPC integration
├── client.py      # PyRPC client implementation
└── README.md      # This file
```

## Running the Example

1. Make sure you have the required dependencies:
```bash
pip install pyrpc[fastapi] uvicorn
```

2. Start the server:
```bash
python server.py
```

3. In another terminal, run the client:
```bash
python client.py
```

## API Documentation

Once the server is running, you can view the API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Available Operations

- `add`: Add two numbers
- `subtract`: Subtract two numbers
- `multiply`: Multiply two numbers
- `divide`: Divide two numbers
- `history`: Get calculation history

## Type Safety

The example demonstrates PyRPC's type safety features:
- Input validation using Pydantic models
- Type-safe procedure calls
- Automatic API documentation
- IDE autocompletion support

## Error Handling

The example includes basic error handling:
- Division by zero protection
- Try-catch block in the client
- Type validation errors 