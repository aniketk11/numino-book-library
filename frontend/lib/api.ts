const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Request failed");
  }
  return res.json() as Promise<T>;
}

// ── Types ────────────────────────────────────────────────────────────────────

export interface Book {
  id: number;
  title: string;
  author: string;
  isbn: string | null;
  total_copies: number;
  available_copies: number;
  created_at: string;
  updated_at: string;
}

export interface Member {
  id: number;
  name: string;
  email: string;
  phone: string | null;
  created_at: string;
  updated_at: string;
}

export interface Borrowing {
  id: number;
  book_id: number;
  member_id: number;
  borrowed_at: string;
  due_date: string;
  returned_at: string | null;
  is_overdue: boolean;
  fine: number;
  book_title: string | null;
  member_name: string | null;
}

// ── Books ────────────────────────────────────────────────────────────────────

export const api = {
  books: {
    list: (q?: string, available?: boolean) => {
      const params = new URLSearchParams();
      if (q) params.set("q", q);
      if (available !== undefined) params.set("available", String(available));
      const qs = params.toString();
      return request<Book[]>(`/books${qs ? `?${qs}` : ""}`);
    },
    create: (data: { title: string; author: string; isbn?: string; total_copies: number }) =>
      request<Book>("/books", { method: "POST", body: JSON.stringify(data) }),
    update: (id: number, data: Partial<{ title: string; author: string; isbn: string; total_copies: number }>) =>
      request<Book>(`/books/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  },

  members: {
    list: () => request<Member[]>("/members"),
    create: (data: { name: string; email: string; phone?: string }) =>
      request<Member>("/members", { method: "POST", body: JSON.stringify(data) }),
    update: (id: number, data: Partial<{ name: string; email: string; phone: string }>) =>
      request<Member>(`/members/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
    borrowings: (id: number) => request<Borrowing[]>(`/members/${id}/borrowings`),
  },

  borrowings: {
    list: (params?: { member_id?: number; book_id?: number; status?: "active" | "overdue" | "returned" }) => {
      const qs = new URLSearchParams();
      if (params?.member_id) qs.set("member_id", String(params.member_id));
      if (params?.book_id) qs.set("book_id", String(params.book_id));
      if (params?.status) qs.set("status", params.status);
      return request<Borrowing[]>(`/borrowings${qs.toString() ? `?${qs}` : ""}`);
    },
    borrow: (book_id: number, member_id: number, due_date?: string) =>
      request<Borrowing>("/borrowings", { method: "POST", body: JSON.stringify({ book_id, member_id, due_date }) }),
    return: (borrowing_id: number) =>
      request<Borrowing>(`/borrowings/${borrowing_id}/return`, { method: "POST" }),
  },
};
