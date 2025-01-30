"""Example calculator server using PyRPC"""
from pydantic import BaseModel
from pyrpc.typed_router import t, procedure

class AddInput(BaseModel):
    a: int
    b: int

class AddOutput(BaseModel):
    result: int

class CalculatorAPI:
    async def add(self, input: AddInput) -> AddOutput:
        """Add two numbers"""
        return AddOutput(result=input.a + input.b)

# Create router from API class
router = t(CalculatorAPI)

if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router.router, prefix="/api")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)