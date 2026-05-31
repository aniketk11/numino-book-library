def test_create_member(client):
    r = client.post("/members", json={"name": "Alice", "email": "alice@lib.com"})
    assert r.status_code == 201
    assert r.json()["name"] == "Alice"


def test_create_member_duplicate_email(client):
    client.post("/members", json={"name": "Alice", "email": "same@lib.com"})
    r = client.post("/members", json={"name": "Bob", "email": "same@lib.com"})
    assert r.status_code == 409


def test_list_members(client):
    client.post("/members", json={"name": "Alice", "email": "a@lib.com"})
    client.post("/members", json={"name": "Bob", "email": "b@lib.com"})
    r = client.get("/members")
    assert len(r.json()) == 2


def test_get_member_not_found(client):
    r = client.get("/members/999")
    assert r.status_code == 404


def test_update_member(client):
    r = client.post("/members", json={"name": "Alice", "email": "alice@lib.com"})
    mid = r.json()["id"]
    r2 = client.patch(f"/members/{mid}", json={"phone": "555-1234"})
    assert r2.status_code == 200
    assert r2.json()["phone"] == "555-1234"
