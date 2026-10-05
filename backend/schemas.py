from decimal import Decimal
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator

class Input(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

class Named(Input):
    name: str = Field(min_length=1, max_length=120)

class WarehouseInput(Named):
    address: str = Field(default='', max_length=250)

class ProductInput(Named):
    sku: str = Field(min_length=1, max_length=64)
    category_id: int | None = Field(default=None, gt=0)
    price: Decimal = Field(default=Decimal('0'), ge=0, max_digits=14, decimal_places=2)

    @field_validator('sku')
    @classmethod
    def uppercase_sku(cls, value):
        return value.upper()

class MovementInput(Input):
    request_id: UUID
    product_id: int = Field(gt=0)
    warehouse_id: int = Field(gt=0)
    kind: Literal['entry', 'exit']
    quantity: Decimal = Field(gt=0, max_digits=14, decimal_places=3)
    reason_id: int = Field(gt=0)
    responsible_id: int = Field(gt=0)
    recipient_id: int | None = Field(default=None, gt=0)
    reference: str = Field(default="", max_length=120)

class ReasonInput(Named):
    kind: Literal['entry', 'exit', 'both']
    active: bool = True

class ResponsibleInput(Named):
    employee_code: str = Field(min_length=1, max_length=64)
    sector: str = Field(default='', max_length=120)
    active: bool = True

    @field_validator('employee_code')
    @classmethod
    def uppercase_code(cls, value):
        return value.upper()

class RecipientCompanyInput(Named):
    active: bool = True

class RecipientInput(Named):
    company_id: int | None = Field(default=None, gt=0)
    active: bool = True
