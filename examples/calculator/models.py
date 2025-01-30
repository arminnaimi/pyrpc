from pydantic import BaseModel, Field, field_validator
from typing import Literal, List, TypeVar, Generic, Callable, Awaitable, Any
from enum import Enum, auto
from dataclasses import dataclass

class CalculatorProcedures(str, Enum):
    """All available calculator procedures"""
    ADD = "add"
    SUBTRACT = "subtract"
    MULTIPLY = "multiply"
    DIVIDE = "divide"
    HISTORY = "history"

class CalculationInput(BaseModel):
    a: float = Field(..., strict=True)
    b: float = Field(..., strict=True)

class CalculationOutput(BaseModel):
    result: float
    operation: str

class HistoryEntry(BaseModel):
    operation: str
    a: float
    b: float
    result: float

class GetHistoryInput(BaseModel):
    limit: int = 10

class HistoryResponse(BaseModel):
    entries: List[HistoryEntry]

# Type-safe router definition
Input = TypeVar("Input", bound=BaseModel)
Output = TypeVar("Output", bound=BaseModel)

@dataclass
class Procedure(Generic[Input, Output]):
    name: str
    input_type: type[Input]
    output_type: type[Output]
    handler: Callable[[Input], Awaitable[Output]]

class CalculatorRouter:
    """Type-safe calculator router definition"""
    def __init__(self):
        self.procedures: dict[str, Procedure] = {}

    def procedure(self, name: str, input_type: type[Input], output_type: type[Output]) -> Callable[[Callable[[Input], Awaitable[Output]]], Procedure[Input, Output]]:
        def decorator(handler: Callable[[Input], Awaitable[Output]]) -> Procedure[Input, Output]:
            proc = Procedure(name, input_type, output_type, handler)
            self.procedures[name] = proc
            return proc
        return decorator

# Create the router instance
calculator = CalculatorRouter() 