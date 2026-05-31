CREATE TABLE IF NOT EXISTS books (
    id          SERIAL PRIMARY KEY,
    title       TEXT NOT NULL,
    author      TEXT NOT NULL,
    isbn        TEXT UNIQUE,
    total_copies INT NOT NULL DEFAULT 1 CHECK (total_copies >= 0),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS members (
    id         SERIAL PRIMARY KEY,
    name       TEXT NOT NULL,
    email      TEXT UNIQUE NOT NULL,
    phone      TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS borrowings (
    id          SERIAL PRIMARY KEY,
    book_id     INT NOT NULL REFERENCES books(id),
    member_id   INT NOT NULL REFERENCES members(id),
    borrowed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    due_date    TIMESTAMPTZ NOT NULL,
    returned_at TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_borrowings_book_id    ON borrowings (book_id);
CREATE INDEX IF NOT EXISTS idx_borrowings_member_id  ON borrowings (member_id);
-- Fast active-loan lookups (availability check, overdue queries)
CREATE INDEX IF NOT EXISTS idx_borrowings_active     ON borrowings (book_id) WHERE returned_at IS NULL;

-- Auto-update updated_at on books and members
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER books_updated_at
    BEFORE UPDATE ON books
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER members_updated_at
    BEFORE UPDATE ON members
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ── Seed data ─────────────────────────────────────────────────────────────────

INSERT INTO books (title, author, isbn, total_copies) VALUES
    ('Dune',                    'Frank Herbert',    '9780441013593', 3),
    ('The Pragmatic Programmer', 'David Thomas',    '9780135957059', 2),
    ('Clean Code',               'Robert C. Martin','9780132350884', 2),
    ('The Great Gatsby',         'F. Scott Fitzgerald', '9780743273565', 1),
    ('1984',                     'George Orwell',   '9780451524935', 2);

INSERT INTO members (name, email, phone) VALUES
    ('Aniket Kapse', 'aniket@library.example',   '555-0101'),
    ('Netra Pelapkar',     'netra@library.example',     '555-0102'),
    ('Nikhil Patil',   'nikhil@library.example',   NULL);

INSERT INTO borrowings (book_id, member_id, borrowed_at, due_date, returned_at) VALUES
    -- Aniket has Dune out (active)
    (1, 1, now() - interval '3 days',  now() + interval '11 days', NULL),
    -- Netra has The Pragmatic Programmer out (active)
    (2, 2, now() - interval '5 days',  now() + interval '9 days',  NULL),
    -- Nikhil has 1984 out and overdue
    (5, 3, now() - interval '20 days', now() - interval '6 days',  NULL),
    -- Aniket returned Clean Code last week
    (3, 1, now() - interval '10 days', now() - interval '3 days',  now() - interval '4 days'),
    -- Netra returned The Great Gatsby yesterday
    (4, 2, now() - interval '8 days',  now() + interval '6 days',  now() - interval '1 day');
