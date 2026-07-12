from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class PersonCreate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, min_length=1, max_length=50)
    status: str = Field(default="active", min_length=1, max_length=50)

    @model_validator(mode="after")
    def require_name(self):
        if not self.display_name and not (self.first_name or self.last_name):
            raise ValueError("first_name, last_name, or display_name is required")
        return self

    def resolved_display_name(self) -> str:
        return self.display_name or " ".join(part for part in [self.first_name, self.last_name] if part)


class PersonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    first_name: str | None
    last_name: str | None
    display_name: str
    email: EmailStr | None
    phone: str | None
    status: str
    created_at: datetime
    updated_at: datetime
