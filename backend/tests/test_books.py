def test_create_book(client):
    r = client.post("/books", json={"title": "Dune", "author": "Frank Herbert", "total_copies": 3})
    assert r.status_code == 201
    data = r.json()
    assert data["title"] == "Dune"
    assert data["total_copies"] == 3
    assert data["available_copies"] == 3


def test_create_book_duplicate_isbn(client):
    client.post("/books", json={"title": "A", "author": "B", "isbn": "123"})
    r = client.post("/books", json={"title": "C", "author": "D", "isbn": "123"})
    assert r.status_code == 409


def test_list_books(client):
    client.post("/books", json={"title": "Dune", "author": "Herbert"})
    client.post("/books", json={"title": "Foundation", "author": "Asimov"})
    r = client.get("/books")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_search_books(client):
    client.post("/books", json={"title": "Dune", "author": "Herbert"})
    client.post("/books", json={"title": "Foundation", "author": "Asimov"})
    r = client.get("/books?q=Dune")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["title"] == "Dune"


def test_get_book_not_found(client):
    r = client.get("/books/999")
    assert r.status_code == 404


def test_update_book(client):
    r = client.post("/books", json={"title": "Old Title", "author": "Auth"})
    book_id = r.json()["id"]
    r2 = client.patch(f"/books/{book_id}", json={"title": "New Title"})
    assert r2.status_code == 200
    assert r2.json()["title"] == "New Title"


def test_available_filter(client):
    r = client.post("/books", json={"title": "Solo Copy", "author": "A", "total_copies": 1})
    book_id = r.json()["id"]
    client.post("/members", json={"name": "Alice", "email": "alice@test.com"})
    client.post("/borrowings", json={"book_id": book_id, "member_id": 1})

    r2 = client.get("/books?available=true")
    ids = [b["id"] for b in r2.json()]
    assert book_id not in ids
