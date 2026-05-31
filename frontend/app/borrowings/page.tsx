"use client";

import { useEffect, useState } from "react";
import { api, Book, Member, Borrowing } from "@/lib/api";

type StatusFilter = "all" | "active" | "overdue" | "returned";

export default function BorrowingsPage() {
  const [books, setBooks] = useState<Book[]>([]);
  const [members, setMembers] = useState<Member[]>([]);
  const [borrowings, setBorrowings] = useState<Borrowing[]>([]);
  const [status, setStatus] = useState<StatusFilter>("all");
  const [error, setError] = useState("");

  const defaultDueDate = () => {
    const d = new Date();
    d.setDate(d.getDate() + 14);
    return d.toISOString().split("T")[0];
  };

  const [form, setForm] = useState({ book_id: "", member_id: "", due_date: defaultDueDate() });

  const loadRefs = async () => {
    const [b, m] = await Promise.all([api.books.list(), api.members.list()]);
    setBooks(b);
    setMembers(m);
  };

  const loadBorrowings = async () => {
    try {
      const s = status === "all" ? undefined : status;
      setBorrowings(await api.borrowings.list({ status: s }));
      setError("");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load borrowings");
    }
  };

  useEffect(() => { loadRefs(); }, []);
  useEffect(() => { loadBorrowings(); }, [status]);

  const handleBorrow = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await api.borrowings.borrow(Number(form.book_id), Number(form.member_id), form.due_date);
      setForm({ book_id: "", member_id: "", due_date: defaultDueDate() });
      loadRefs();
      loadBorrowings();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to borrow book");
    }
  };

  const handleReturn = async (borrowingId: number) => {
    setError("");
    try {
      await api.borrowings.return(borrowingId);
      loadRefs();
      loadBorrowings();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to return book");
    }
  };

  const fmtDate = (iso: string) => new Date(iso).toLocaleDateString("en-GB");

  return (
    <main className="max-w-5xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Borrowings</h1>

      {error && <p className="text-red-600 mb-4 p-2 bg-red-50 rounded">{error}</p>}

      {/* Borrow form */}
      <form onSubmit={handleBorrow} className="mb-8 p-4 border rounded bg-gray-50 space-y-3">
        <h2 className="font-semibold">Borrow a Book</h2>
        <div className="grid grid-cols-2 gap-3">
          <select required value={form.member_id}
            onChange={e => setForm({ ...form, member_id: e.target.value })}
            className="border p-2 rounded">
            <option value="">— Select member —</option>
            {members.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
          </select>
          <select required value={form.book_id}
            onChange={e => setForm({ ...form, book_id: e.target.value })}
            className="border p-2 rounded">
            <option value="">— Select book —</option>
            {books.filter(b => b.available_copies > 0).map(b => (
              <option key={b.id} value={b.id}>{b.title} ({b.available_copies} left)</option>
            ))}
          </select>
        </div>
        <div className="flex flex-col gap-1 w-fit">
          <label className="text-sm text-gray-600">Due Date</label>
          <input type="date" required
            value={form.due_date}
            min={new Date(Date.now() + 86400000).toISOString().split("T")[0]}
            onChange={e => setForm({ ...form, due_date: e.target.value })}
            className="border p-2 rounded" />
        </div>
        <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
          Borrow
        </button>
      </form>

      {/* Status filter */}
      <div className="flex gap-2 mb-4">
        {(["all", "active", "overdue", "returned"] as StatusFilter[]).map(s => (
          <button key={s} onClick={() => setStatus(s)}
            className={`px-3 py-1 rounded border text-sm capitalize ${status === s ? "bg-blue-600 text-white border-blue-600" : "hover:bg-gray-100"}`}>
            {s}
          </button>
        ))}
      </div>

      {/* Borrowings table */}
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="bg-gray-100 text-left">
            <th className="border px-3 py-2">Member</th>
            <th className="border px-3 py-2">Book</th>
            <th className="border px-3 py-2">Borrowed</th>
            <th className="border px-3 py-2">Due</th>
            <th className="border px-3 py-2">Status</th>
            <th className="border px-3 py-2">Fine</th>
            <th className="border px-3 py-2"></th>
          </tr>
        </thead>
        <tbody>
          {borrowings.map(b => (
            <tr key={b.id} className={b.is_overdue ? "bg-red-50" : "hover:bg-gray-50"}>
              <td className="border px-3 py-2">{b.member_name ?? b.member_id}</td>
              <td className="border px-3 py-2">{b.book_title ?? b.book_id}</td>
              <td className="border px-3 py-2">{fmtDate(b.borrowed_at)}</td>
              <td className="border px-3 py-2">{fmtDate(b.due_date)}</td>
              <td className="border px-3 py-2">
                {b.returned_at
                  ? <span className="text-gray-500">Returned {fmtDate(b.returned_at)}</span>
                  : b.is_overdue
                    ? <span className="text-red-600 font-semibold">Overdue</span>
                    : <span className="text-green-700">Active</span>}
              </td>
              <td className="border px-3 py-2">
                {b.fine > 0 ? <span className="text-red-600">₹{b.fine.toFixed(2)}</span> : "—"}
              </td>
              <td className="border px-3 py-2">
                {!b.returned_at && (
                  <button onClick={() => handleReturn(b.id)}
                    className="text-sm bg-green-600 text-white px-2 py-1 rounded hover:bg-green-700">
                    Return
                  </button>
                )}
              </td>
            </tr>
          ))}
          {borrowings.length === 0 && (
            <tr><td colSpan={7} className="border px-3 py-4 text-center text-gray-400">No borrowings found</td></tr>
          )}
        </tbody>
      </table>
    </main>
  );
}
