from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Book
from app.schemas import BookCreate, BookUpdate, BookOut
from app.services.borrowing_service import get_available_copies

router = APIRouter(prefix="/books", tags=["books"])


def _book_out(book: Book, db: Session) -> BookOut:
    return BookOut(
        id=book.id,
        title=book.title,
        author=book.author,
        isbn=book.isbn,
        total_copies=book.total_copies,
        available_copies=get_available_copies(db, book),
        created_at=book.created_at,
        updated_at=book.updated_at,
    )


@router.post("", response_model=BookOut, status_code=201)
def create_book(payload: BookCreate, db: Session = Depends(get_db)):
    if payload.isbn:
        existing = db.scalar(select(Book).where(Book.isbn == payload.isbn))
        if existing:
            raise HTTPException(status_code=409, detail="A book with this ISBN already exists")

    book = Book(**payload.model_dump())
    db.add(book)
    db.commit()
    db.refresh(book)
    return _book_out(book, db)


@router.get("", response_model=list[BookOut])
def list_books(
    q: Optional[str] = None,
    available: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    stmt = select(Book)
    if q:
        stmt = stmt.where(or_(Book.title.ilike(f"%{q}%"), Book.author.ilike(f"%{q}%")))
    books = db.scalars(stmt).all()

    result = [_book_out(b, db) for b in books]
    if available is True:
        result = [b for b in result if b.available_copies > 0]
    return result


@router.get("/{book_id}", response_model=BookOut)
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return _book_out(book, db)


@router.patch("/{book_id}", response_model=BookOut)
def update_book(book_id: int, payload: BookUpdate, db: Session = Depends(get_db)):
    book = db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    if payload.isbn and payload.isbn != book.isbn:
        existing = db.scalar(select(Book).where(Book.isbn == payload.isbn))
        if existing:
            raise HTTPException(status_code=409, detail="A book with this ISBN already exists")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(book, field, value)

    db.commit()
    db.refresh(book)
    return _book_out(book, db)
