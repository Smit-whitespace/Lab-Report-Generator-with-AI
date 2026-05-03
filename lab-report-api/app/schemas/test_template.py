from pydantic import BaseModel
from typing import List, Dict


class Parameter(BaseModel):
    name: str
    unit: str


class TestTemplateCreate(BaseModel):
    name: str
    parameters: List[Parameter]


class TestTemplateUpdate(BaseModel):
    name: str | None = None
    parameters: List[Parameter] | None = None


class TestTemplateResponse(BaseModel):
    id: int
    created_by_user_id: int | None
    name: str
    parameters: List[Parameter]

    class Config:
        from_attributes = True
