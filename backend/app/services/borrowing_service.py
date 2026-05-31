from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Book, Borrowing


def count_active_borrowings(db: Session, book_id: int) -> int:
    return db.scalar(
        select(func.count())
        .where(Borrowing.book_id == book_id, Borrowing.returned_at.is_(None))
    ) or 0


def get_available_copies(db: Session, book: Book) -> int:
    return book.total_copies - count_active_borrowings(db, book.id)


def borrow_book(db: Session, book_id: int, member_id: int, due_date: datetime | None = None) -> Borrowing:
    from app.models import Member
    from fastapi import HTTPException

    # Lock the book row to prevent concurrent over-borrow (SELECT ... FOR UPDATE).
    # Without this, two simultaneous requests could both pass the availability check
    # and both create a borrowing when only one copy remains.
    book = db.execute(
        select(Book).where(Book.id == book_id).with_for_update()
    ).scalar_one_or_none()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    member = db.get(Member, member_id)
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")

    available = get_available_copies(db, book)
    if available <= 0:
        raise HTTPException(
            status_code=409,
            detail=f"No copies of '{book.title}' are currently available"
        )

    now = datetime.now(timezone.utc)
    from datetime import timedelta
    resolved_due = due_date if due_date else now + timedelta(days=settings.loan_period_days)
    borrowing = Borrowing(
        book_id=book_id,
        member_id=member_id,
        borrowed_at=now,
        due_date=resolved_due,
    )
    db.add(borrowing)
    db.commit()
    db.refresh(borrowing)
    return borrowing


def return_book(db: Session, borrowing_id: int) -> Borrowing:
    from fastapi import HTTPException

    borrowing = db.get(Borrowing, borrowing_id)
    if borrowing is None:
        raise HTTPException(status_code=404, detail="Borrowing not found")
    if borrowing.returned_at is not None:
        raise HTTPException(status_code=409, detail="This borrowing has already been returned")

    borrowing.returned_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(borrowing)
    return borrowing


def compute_borrowing_derived(borrowing: Borrowing) -> tuple[bool, float]:
    """Return (is_overdue, fine_amount)."""
    now = datetime.now(timezone.utc)
    due = borrowing.due_date
    if due.tzinfo is None:
        due = due.replace(tzinfo=timezone.utc)

    if borrowing.returned_at is not None:
        return False, 0.0

    is_overdue = now > due
    if not is_overdue:
        return False, 0.0

    days_overdue = (now - due).days
    fine = round(days_overdue * settings.daily_fine_rate, 2)
    return True, fine
