from typing import Any

from pydantic import BaseModel


class MappingRequest(BaseModel):
    id: int
    first_name: str
    last_name: str
    salary: float | int
    email: str


class MappingResponse(BaseModel):
    id: int
    name: str
    email: str
