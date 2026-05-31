from datetime import datetime, timezone, timedelta
from app.models import Borrowing


def _seed(client):
    book = client.post("/books", json={"title": "Dune", "author": "Herbert", "total_copies": 2}).json()
    member = client.post("/members", json={"name": "Alice", "email": "alice@lib.com"}).json()
    return book["id"], member["id"]


def test_borrow_book(client):
    bid, mid = _seed(client)
    r = client.post("/borrowings", json={"book_id": bid, "member_id": mid})
    assert r.status_code == 201
    data = r.json()
    assert data["book_id"] == bid
    assert data["member_id"] == mid
    assert data["returned_at"] is None
    assert data["is_overdue"] is False
    assert data["fine"] == 0.0


def test_borrow_reduces_available_copies(client):
    bid, mid = _seed(client)
    client.post("/borrowings", json={"book_id": bid, "member_id": mid})
    r = client.get(f"/books/{bid}")
    assert r.json()["available_copies"] == 1


def test_borrow_no_copies_available(client):
    book = client.post("/books", json={"title": "Solo", "author": "X", "total_copies": 1}).json()
    m1 = client.post("/members", json={"name": "A", "email": "a@lib.com"}).json()
    m2 = client.post("/members", json={"name": "B", "email": "b@lib.com"}).json()

    client.post("/borrowings", json={"book_id": book["id"], "member_id": m1["id"]})
    r = client.post("/borrowings", json={"book_id": book["id"], "member_id": m2["id"]})
    assert r.status_code == 409


def test_borrow_nonexistent_book(client):
    client.post("/members", json={"name": "A", "email": "a@lib.com"})
    r = client.post("/borrowings", json={"book_id": 999, "member_id": 1})
    assert r.status_code == 404


def test_borrow_nonexistent_member(client):
    bid, _ = _seed(client)
    r = client.post("/borrowings", json={"book_id": bid, "member_id": 999})
    assert r.status_code == 404


def test_return_book(client):
    bid, mid = _seed(client)
    borrowing = client.post("/borrowings", json={"book_id": bid, "member_id": mid}).json()
    r = client.post(f"/borrowings/{borrowing['id']}/return")
    assert r.status_code == 200
    assert r.json()["returned_at"] is not None


def test_return_already_returned(client):
    bid, mid = _seed(client)
    borrowing = client.post("/borrowings", json={"book_id": bid, "member_id": mid}).json()
    client.post(f"/borrowings/{borrowing['id']}/return")
    r = client.post(f"/borrowings/{borrowing['id']}/return")
    assert r.status_code == 409


def test_return_restores_available_copies(client):
    bid, mid = _seed(client)
    borrowing = client.post("/borrowings", json={"book_id": bid, "member_id": mid}).json()
    client.post(f"/borrowings/{borrowing['id']}/return")
    r = client.get(f"/books/{bid}")
    assert r.json()["available_copies"] == 2


def test_list_borrowings_filter_by_member(client):
    bid, mid = _seed(client)
    m2 = client.post("/members", json={"name": "Bob", "email": "bob@lib.com"}).json()
    client.post("/borrowings", json={"book_id": bid, "member_id": mid})
    client.post("/borrowings", json={"book_id": bid, "member_id": m2["id"]})
    r = client.get(f"/borrowings?member_id={mid}")
    assert len(r.json()) == 1


def test_member_borrowings_endpoint(client):
    bid, mid = _seed(client)
    client.post("/borrowings", json={"book_id": bid, "member_id": mid})
    r = client.get(f"/members/{mid}/borrowings")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["book_title"] == "Dune"


def test_overdue_borrowing_shows_fine(client):
    from tests.conftest import TestingSession
    from app.config import settings

    bid, mid = _seed(client)
    borrowing_r = client.post("/borrowings", json={"book_id": bid, "member_id": mid})
    borrowing_id = borrowing_r.json()["id"]

    # Backdate the due_date so the borrowing is overdue
    past_due = datetime.now(timezone.utc) - timedelta(days=3)
    with TestingSession() as db:
        borrowing = db.get(Borrowing, borrowing_id)
        borrowing.due_date = past_due
        db.commit()

    r = client.get("/borrowings?status=overdue")
    assert r.status_code == 200
    overdue = [b for b in r.json() if b["id"] == borrowing_id]
    assert len(overdue) == 1
    assert overdue[0]["is_overdue"] is True
    expected_fine = round(3 * settings.daily_fine_rate, 2)
    assert overdue[0]["fine"] == expected_fine


def test_list_borrowings_status_returned(client):
    bid, mid = _seed(client)
    borrowing = client.post("/borrowings", json={"book_id": bid, "member_id": mid}).json()
    client.post(f"/borrowings/{borrowing['id']}/return")
    r = client.get("/borrowings?status=returned")
    assert r.status_code == 200
    assert all(b["returned_at"] is not None for b in r.json())
