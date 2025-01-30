from pyrpc import PyRPCClient, ClientConfig
from models import CalculationInput, CalculationOutput, GetHistoryInput, HistoryEntry
from typing import List

async def main():
    # Create client
    client = PyRPCClient(
        ClientConfig(base_url="http://localhost:8000/pyrpc")
    )
    
    # Create type-safe procedures
    calculator = client.caller("calculator")
    add = calculator.procedure("add", CalculationInput, CalculationOutput)
    subtract = calculator.procedure("subtract", CalculationInput, CalculationOutput)
    multiply = calculator.procedure("multiply", CalculationInput, CalculationOutput)
    divide = calculator.procedure("divide", CalculationInput, CalculationOutput)
    history = calculator.procedure("history", GetHistoryInput, List[HistoryEntry])
    
    try:
        # Perform some calculations
        result = await add({"a": 5, "b": 3})
        print(f"5 + 3 = {result.result}")
        
        result = await multiply({"a": 4, "b": 6})
        print(f"4 * 6 = {result.result}")
        
        result = await subtract({"a": 10, "b": 7})
        print(f"10 - 7 = {result.result}")
        
        result = await divide({"a": 15, "b": 3})
        print(f"15 / 3 = {result.result}")
        
        # Get calculation history
        calc_history = await history({"limit": 5})
        print("\nLast 5 calculations:")
        for entry in calc_history:
            print(f"{entry.a} {entry.operation} {entry.b} = {entry.result}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 