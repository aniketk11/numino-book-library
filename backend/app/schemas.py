from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator


# ── Books ─────────────────────────────────────────────────────────────────────

class BookCreate(BaseModel):
    title: str
    author: str
    isbn: Optional[str] = None
    total_copies: int = 1

    @field_validator("total_copies")
    @classmethod
    def copies_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("total_copies must be at least 1")
        return v


class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    isbn: Optional[str] = None
    total_copies: Optional[int] = None

    @field_validator("total_copies")
    @classmethod
    def copies_positive(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 1:
            raise ValueError("total_copies must be at least 1")
        return v


class BookOut(BaseModel):
    id: int
    title: str
    author: str
    isbn: Optional[str]
    total_copies: int
    available_copies: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Members ───────────────────────────────────────────────────────────────────

class MemberCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None


class MemberUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class MemberOut(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Loans ─────────────────────────────────────────────────────────────────────

class BorrowingCreate(BaseModel):
    book_id: int
    member_id: int
    due_date: Optional[datetime] = None


class BorrowingOut(BaseModel):
    id: int
    book_id: int
    member_id: int
    borrowed_at: datetime
    due_date: datetime
    returned_at: Optional[datetime]
    is_overdue: bool
    fine: float
    book_title: Optional[str] = None
    member_name: Optional[str] = None

    model_config = {"from_attributes": True}
