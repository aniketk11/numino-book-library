"use client";

import { useEffect, useState } from "react";
import { api, Book } from "@/lib/api";

export default function BooksPage() {
  const [books, setBooks] = useState<Book[]>([]);
  const [q, setQ] = useState("");
  const [error, setError] = useState("");

  const [form, setForm] = useState({ title: "", author: "", isbn: "", total_copies: 1 });
  const [editId, setEditId] = useState<number | null>(null);

  const load = async () => {
    try {
      setBooks(await api.books.list(q || undefined));
      setError("");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load books");
    }
  };

  useEffect(() => { load(); }, [q]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      const payload = {
        title: form.title,
        author: form.author,
        isbn: form.isbn || undefined,
        total_copies: form.total_copies,
      };
      if (editId) {
        await api.books.update(editId, payload);
      } else {
        await api.books.create(payload);
      }
      setForm({ title: "", author: "", isbn: "", total_copies: 1 });
      setEditId(null);
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to save book");
    }
  };

  const startEdit = (book: Book) => {
    setEditId(book.id);
    setForm({ title: book.title, author: book.author, isbn: book.isbn ?? "", total_copies: book.total_copies });
  };

  return (
    <main className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Books</h1>

      {error && <p className="text-red-600 mb-4 p-2 bg-red-50 rounded">{error}</p>}

      {/* Add / Edit form */}
      <form onSubmit={handleSubmit} className="mb-8 p-4 border rounded bg-gray-50 space-y-3">
        <h2 className="font-semibold">{editId ? "Edit Book" : "Add Book"}</h2>
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1 col-span-2">
            <label className="text-sm text-gray-600">Title</label>
            <input required value={form.title}
              onChange={e => setForm({ ...form, title: e.target.value })}
              className="border p-2 rounded" />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-gray-600">Author</label>
            <input required value={form.author}
              onChange={e => setForm({ ...form, author: e.target.value })}
              className="border p-2 rounded" />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-gray-600">ISBN <span className="text-gray-400">(optional)</span></label>
            <input value={form.isbn}
              onChange={e => setForm({ ...form, isbn: e.target.value })}
              className="border p-2 rounded" />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-gray-600">Total Copies</label>
            <input type="number" min={1} required
              value={form.total_copies}
              onChange={e => setForm({ ...form, total_copies: Number(e.target.value) })}
              className="border p-2 rounded" />
          </div>
        </div>
        <div className="flex gap-2">
          <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
            {editId ? "Update" : "Add Book"}
          </button>
          {editId && (
            <button type="button" onClick={() => { setEditId(null); setForm({ title: "", author: "", isbn: "", total_copies: 1 }); }}
              className="px-4 py-2 border rounded hover:bg-gray-100">Cancel</button>
          )}
        </div>
      </form>

      {/* Search */}
      <input placeholder="Search by title or author…" value={q}
        onChange={e => setQ(e.target.value)}
        className="border p-2 rounded w-full mb-4" />

      {/* Table */}
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="bg-gray-100 text-left">
            <th className="border px-3 py-2">Title</th>
            <th className="border px-3 py-2">Author</th>
            <th className="border px-3 py-2">ISBN</th>
            <th className="border px-3 py-2 text-center">Total</th>
            <th className="border px-3 py-2 text-center">Available</th>
            <th className="border px-3 py-2"></th>
          </tr>
        </thead>
        <tbody>
          {books.map(b => (
            <tr key={b.id} className="hover:bg-gray-50">
              <td className="border px-3 py-2">{b.title}</td>
              <td className="border px-3 py-2">{b.author}</td>
              <td className="border px-3 py-2 text-gray-500">{b.isbn ?? "—"}</td>
              <td className="border px-3 py-2 text-center">{b.total_copies}</td>
              <td className="border px-3 py-2 text-center">
                <span className={b.available_copies === 0 ? "text-red-600 font-medium" : "text-green-700 font-medium"}>
                  {b.available_copies}
                </span>
              </td>
              <td className="border px-3 py-2">
                <button onClick={() => startEdit(b)} className="text-blue-600 hover:underline text-xs">Edit</button>
              </td>
            </tr>
          ))}
          {books.length === 0 && (
            <tr><td colSpan={6} className="border px-3 py-4 text-center text-gray-400">No books found</td></tr>
          )}
        </tbody>
      </table>
    </main>
  );
}
