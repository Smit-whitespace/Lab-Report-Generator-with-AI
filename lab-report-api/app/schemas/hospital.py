from pydantic import BaseModel, EmailStr


class HospitalCreate(BaseModel):
    name: str
    address: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    registration_number: str | None = None


class HospitalResponse(BaseModel):
    id: int
    name: str
    address: str | None
    phone: str | None
    email: EmailStr | None
    registration_number: str | None
    updated_at: str

    class Config:
        from_attributes = True
