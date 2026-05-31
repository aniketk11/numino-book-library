"""
sample_client.py — demonstrates the full happy-path flow via the REST API.

Usage:
    python sample_client.py [BASE_URL]

    BASE_URL defaults to http://localhost:8000
"""
import sys
import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"


def step(label: str, response: httpx.Response) -> dict:
    print(f"\n{'─' * 60}")
    print(f"  {label}")
    print(f"  {response.request.method} {response.url}  →  {response.status_code}")
    data = response.json()
    import json
    print(json.dumps(data, indent=2, default=str))
    response.raise_for_status()
    return data


def main():
    c = httpx.Client(base_url=BASE, timeout=10)

    # 1. Create a book with 2 copies (no ISBN to avoid clashes with seed data)
    book = step(
        "Create book: The Hitchhiker's Guide (2 copies)",
        c.post("/books", json={"title": "The Hitchhiker's Guide to the Galaxy", "author": "Douglas Adams", "total_copies": 2}),
    )

    # 2. Create two members (unique emails to avoid clashes with seed data)
    alice = step("Create member: Alice", c.post("/members", json={"name": "Alice", "email": "alice@sample.example"}))
    bob   = step("Create member: Bob",   c.post("/members", json={"name": "Bob",   "email": "bob@sample.example"}))

    # 3. Both borrow the book (2 copies available)
    loan1 = step("Alice borrows the book", c.post("/borrowings", json={"book_id": book["id"], "member_id": alice["id"]}))
    loan2 = step("Bob borrows the book",   c.post("/borrowings", json={"book_id": book["id"], "member_id": bob["id"]}))

    # 4. Check availability — should now be 0
    step("Book detail (expect available_copies=0)", c.get(f"/books/{book['id']}"))

    # 5. Third borrow attempt — expect 409
    print(f"\n{'─' * 60}")
    print("  Attempt to borrow last copy (expect 409 Conflict)")
    r = c.post("/borrowings", json={"book_id": book["id"], "member_id": alice["id"]})
    print(f"  POST /borrowings  →  {r.status_code}  (expected 409)")
    print(f"  {r.json()['detail']}")

    # 6. Alice returns the book
    step("Alice returns the book", c.post(f"/borrowings/{loan1['id']}/return"))

    # 7. List all loans for the book
    step("List all loans for the book", c.get(f"/borrowings?book_id={book['id']}"))

    # 8. List active loans for Bob
    step("Bob's active loans", c.get(f"/members/{bob['id']}/borrowings"))

    print(f"\n{'─' * 60}")
    print("  All steps completed successfully.")


if __name__ == "__main__":
    main()
