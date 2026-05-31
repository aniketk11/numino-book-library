from typing import Optional, Literal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Borrowing
from app.schemas import BorrowingCreate, BorrowingOut
from app.services.borrowing_service import borrow_book, return_book, compute_borrowing_derived

router = APIRouter(tags=["borrowings"])


def _borrowing_out(borrowing: Borrowing) -> BorrowingOut:
    is_overdue, fine = compute_borrowing_derived(borrowing)
    return BorrowingOut(
        id=borrowing.id,
        book_id=borrowing.book_id,
        member_id=borrowing.member_id,
        borrowed_at=borrowing.borrowed_at,
        due_date=borrowing.due_date,
        returned_at=borrowing.returned_at,
        is_overdue=is_overdue,
        fine=fine,
        book_title=borrowing.book.title if borrowing.book else None,
        member_name=borrowing.member.name if borrowing.member else None,
    )


def _load_borrowing_with_relations(db: Session, borrowing_id: int) -> Borrowing:
    borrowing = db.scalar(
        select(Borrowing)
        .where(Borrowing.id == borrowing_id)
        .options(joinedload(Borrowing.book), joinedload(Borrowing.member))
    )
    if not borrowing:
        raise HTTPException(status_code=404, detail="Borrowing not found")
    return borrowing


@router.post("/borrowings", response_model=BorrowingOut, status_code=201)
def create_borrowing(payload: BorrowingCreate, db: Session = Depends(get_db)):
    borrowing = borrow_book(db, payload.book_id, payload.member_id, payload.due_date)
    return _borrowing_out(_load_borrowing_with_relations(db, borrowing.id))


@router.post("/borrowings/{borrowing_id}/return", response_model=BorrowingOut)
def return_borrowing(borrowing_id: int, db: Session = Depends(get_db)):
    borrowing = return_book(db, borrowing_id)
    return _borrowing_out(_load_borrowing_with_relations(db, borrowing.id))


@router.get("/borrowings", response_model=list[BorrowingOut])
def list_borrowings(
    member_id: Optional[int] = None,
    book_id: Optional[int] = None,
    status: Optional[Literal["active", "overdue", "returned"]] = None,
    db: Session = Depends(get_db),
):
    stmt = select(Borrowing).options(joinedload(Borrowing.book), joinedload(Borrowing.member))
    if member_id:
        stmt = stmt.where(Borrowing.member_id == member_id)
    if book_id:
        stmt = stmt.where(Borrowing.book_id == book_id)
    if status == "returned":
        stmt = stmt.where(Borrowing.returned_at.is_not(None))
    elif status in ("active", "overdue"):
        stmt = stmt.where(Borrowing.returned_at.is_(None))

    borrowings = db.scalars(stmt).all()
    result = [_borrowing_out(b) for b in borrowings]

    if status == "overdue":
        result = [b for b in result if b.is_overdue]
    elif status == "active":
        result = [b for b in result if not b.is_overdue]

    return result


@router.get("/members/{member_id}/borrowings", response_model=list[BorrowingOut], tags=["members"])
def get_member_borrowings(member_id: int, db: Session = Depends(get_db)):
    from app.models import Member
    member = db.get(Member, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    borrowings = db.scalars(
        select(Borrowing)
        .where(Borrowing.member_id == member_id, Borrowing.returned_at.is_(None))
        .options(joinedload(Borrowing.book), joinedload(Borrowing.member))
    ).all()
    return [_borrowing_out(b) for b in borrowings]
