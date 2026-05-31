# Neighborhood Library Service

A REST API + minimal web UI for managing a neighborhood library's books, members, and lending operations.

**Stack:** Python 3.12 · FastAPI · PostgreSQL 16 · SQLAlchemy 2 · Next.js 15 (App Router) · Docker Compose

---

## Quick Start

```bash
docker compose up --build
```

| Service  | URL                              | Notes                        |
|----------|----------------------------------|------------------------------|
| Frontend | http://localhost:3000            | Next.js UI                   |
| API      | http://localhost:8000            | FastAPI                      |
| Swagger  | http://localhost:8000/docs       | Interactive API docs         |
| Postgres | localhost:5432                   | DB: `library`, user: `library` |

---

## Database Schema

```
books
├── id            SERIAL PK
├── title         TEXT NOT NULL
├── author        TEXT NOT NULL
├── isbn          TEXT UNIQUE
├── total_copies  INT DEFAULT 1  ← physical copies owned
├── created_at    TIMESTAMPTZ
└── updated_at    TIMESTAMPTZ    ← auto-updated via trigger

members
├── id         SERIAL PK
├── name       TEXT NOT NULL
├── email      TEXT UNIQUE NOT NULL
├── phone      TEXT
├── created_at TIMESTAMPTZ
└── updated_at TIMESTAMPTZ

borrowings
├── id          SERIAL PK
├── book_id     FK → books.id
├── member_id   FK → members.id
├── borrowed_at TIMESTAMPTZ DEFAULT now()
├── due_date    TIMESTAMPTZ            ← borrowed_at + LOAN_PERIOD_DAYS
├── returned_at TIMESTAMPTZ NULL       ← NULL means still out
└── created_at  TIMESTAMPTZ
```

**Derived fields** (computed on every read, never stored):
- `available_copies` = `total_copies − active borrowings`
- `is_overdue` = `returned_at IS NULL AND due_date < now()`
- `fine` = `max(0, days_overdue) × DAILY_FINE_RATE`

**Schema note:** `db/init.sql` is the DDL source of truth and is mounted into the Postgres container. It runs automatically on first boot. For a production deployment, these would be managed with Alembic migrations to allow zero-data-loss schema evolution and rollback.

---

## API Endpoints

### Books
| Method | Path           | Description                                    |
|--------|----------------|------------------------------------------------|
| POST   | /books         | Create a book                                  |
| GET    | /books         | List books (`?q=`, `?available=true`)          |
| GET    | /books/{id}    | Get book detail (includes `available_copies`)  |
| PATCH  | /books/{id}    | Update book fields                             |

### Members
| Method | Path                | Description                       |
|--------|---------------------|-----------------------------------|
| POST   | /members            | Create a member                   |
| GET    | /members            | List members                      |
| GET    | /members/{id}       | Get member detail                 |
| PATCH  | /members/{id}       | Update member fields              |
| GET    | /members/{id}/borrowings | Active borrowings for a member         |

### Borrowings
| Method | Path               | Description                                                         |
|--------|--------------------|---------------------------------------------------------------------|
| POST   | /borrowings             | Borrow a book `{book_id, member_id}`                               |
| POST   | /borrowings/{id}/return | Return a borrowed book                                              |
| GET    | /borrowings             | List borrowings (`?member_id=`, `?book_id=`, `?status=active\|overdue\|returned`) |

**Error responses:**
- `404` — book, member, or borrowing not found
- `409` — no copies available; borrowing already returned; duplicate email/ISBN
- `422` — Pydantic validation failure (automatic)

---

## Running Tests

Tests use a separate `library_test` database on the same Postgres instance.

```bash
# With the stack running
docker compose run --rm backend pytest -v

# Or locally (requires Postgres running and TEST_DATABASE_URL set)
cd backend
pip install -r requirements.txt
TEST_DATABASE_URL=postgresql://library:library@localhost:5432/library_test pytest -v
```

---

## Sample Client

`backend/sample_client.py` demonstrates the full happy-path via the REST API:
creates a book and two members, borrows all copies, shows a 409 on a third
borrow attempt, then returns a book.

```bash
# With the stack running
docker compose run --rm backend python sample_client.py
# Or locally
python backend/sample_client.py http://localhost:8000
```

---

## Environment Variables

| Variable         | Default                                        | Description                   |
|------------------|------------------------------------------------|-------------------------------|
| DATABASE_URL     | `postgresql://library:library@db:5432/library` | Postgres connection string    |
| LOAN_PERIOD_DAYS | `14`                                           | Days before a loan is due     |
| DAILY_FINE_RATE  | `20`                                         | INR fine per overdue day      |

Set these in `docker-compose.yml` or a `.env` file in `backend/`.

---

## Project Structure

```
backend/
  app/
    main.py            # FastAPI app, CORS, router registration
    config.py          # env-driven settings
    database.py        # SQLAlchemy engine + session dependency
    models.py          # ORM models (mirror init.sql)
    schemas.py         # Pydantic request/response models
    routers/
      books.py         # HTTP layer only
      members.py
      borrowings.py
    services/
      borrowing_service.py  # borrow/return rules, availability, fine calculation
  tests/
    conftest.py        # test DB setup, fixtures
    test_books.py
    test_members.py
    test_borrowings.py
  sample_client.py
  requirements.txt
  Dockerfile
db/
  init.sql             # DDL source of truth
frontend/
  app/
    books/page.tsx
    members/page.tsx
    borrowings/page.tsx
  lib/api.ts           # typed fetch wrappers
docker-compose.yml
```

### `backend/`
The Python FastAPI server. Contains all API logic, database interaction, and business rules.

#### `backend/app/`
The main application package.
- **`main.py`** — creates the FastAPI app instance, registers CORS middleware, and mounts all routers.
- **`config.py`** — reads environment variables (`DATABASE_URL`, `LOAN_PERIOD_DAYS`, `DAILY_FINE_RATE`) using `pydantic-settings`. Defaults are used when env vars are not set.
- **`database.py`** — creates the SQLAlchemy engine and connection pool. Exposes `get_db`, a FastAPI dependency that opens one database session per request and closes it when the request ends.
- **`models.py`** — SQLAlchemy ORM models (`Book`, `Member`, `Borrowing`). Each class maps to a database table. These are used to query and write data.
- **`schemas.py`** — Pydantic models that define the shape of API requests and responses. Separate from ORM models — they handle validation of incoming data and serialization of outgoing JSON.

#### `backend/app/routers/`
One file per resource. Routers handle HTTP only — they parse requests, call services or query the DB, and return responses. No business logic lives here.
- **`books.py`** — `POST /books`, `GET /books`, `GET /books/{id}`, `PATCH /books/{id}`
- **`members.py`** — `POST /members`, `GET /members`, `GET /members/{id}`, `PATCH /members/{id}`, `GET /members/{id}/borrowings`
- **`borrowings.py`** — `POST /borrowings` (borrow), `POST /borrowings/{id}/return`, `GET /borrowings`

#### `backend/app/services/`
Business logic layer, kept separate from HTTP routing.
- **`borrowing_service.py`** — owns all lending rules: availability check with a `SELECT FOR UPDATE` concurrency lock, due date calculation, return validation, and fine computation. Nothing in here knows about HTTP status codes or request/response shapes.

#### `backend/tests/`
pytest test suite. Uses a separate `library_test` Postgres database so tests never touch production data.
- **`conftest.py`** — sets up the test database, overrides the `get_db` dependency to point at the test DB, and provides fixtures that truncate all tables between tests for isolation.
- **`test_books.py`** — tests for book CRUD, search, and availability filtering.
- **`test_members.py`** — tests for member CRUD and duplicate email enforcement.
- **`test_borrowings.py`** — tests for borrow, return, 409 on no copies, 409 on double return, overdue detection, and fine calculation.

#### `backend/sample_client.py`
A standalone script that demonstrates the full happy-path flow via HTTP requests against the running API. Creates a book, two members, borrows all copies, shows a `409` on a third borrow, then returns a book.

Run:
 ```bash
docker compose exec backend python sample_client.py
```
---

### `db/`
Database setup scripts.
- **`init.sql`** — the schema source of truth. Creates all tables, indexes, and triggers. Mounted into the Postgres container and executed automatically on first boot. Also contains seed data (5 books, 3 members, 5 borrowings) pre-loaded for demonstration.

---

### `frontend/`
The Next.js web UI. Communicates with the FastAPI backend over REST.

#### `frontend/app/`
Next.js App Router pages. Each subfolder is a route.
- **`books/page.tsx`** — lists all books with available copy counts, search by title/author, and a create/edit form.
- **`members/page.tsx`** — lists all members and provides a create/edit form.
- **`borrowings/page.tsx`** — borrow form (member + book + due date picker), borrowings table with active/overdue/returned filters, overdue rows highlighted with fine shown in INR, and a Return button.

#### `frontend/lib/`
- **`api.ts`** — typed `fetch` wrappers for every backend endpoint. All API calls go through here, keeping fetch logic out of components.

---

### Root
- **`docker-compose.yml`** — defines and wires all three services (`db`, `backend`, `frontend`). Sets environment variables and ensures startup order via `depends_on` and healthchecks.
