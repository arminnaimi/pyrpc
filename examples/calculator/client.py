"""Example calculator client using PyRPC"""

import asyncio

from server import AddInput, router

from pyrpc.typed_client import create_caller


async def main():
    # Create a type-safe client
    client = create_caller(router, "http://localhost:8000/api")

    # Call the add procedure with type checking
    result = await client.add(AddInput(a=2, b=2))
    print(f"1 + 2 = {result.result}")


if __name__ == "__main__":
    asyncio.run(main())
