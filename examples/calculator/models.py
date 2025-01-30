from pydantic import BaseModel, Field, field_validator
from typing import Literal

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