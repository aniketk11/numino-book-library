"use client";

import { useEffect, useState } from "react";
import { api, Member } from "@/lib/api";

export default function MembersPage() {
  const [members, setMembers] = useState<Member[]>([]);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ name: "", email: "", phone: "" });
  const [editId, setEditId] = useState<number | null>(null);

  const load = async () => {
    try {
      setMembers(await api.members.list());
      setError("");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load members");
    }
  };

  useEffect(() => { load(); }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      const payload = { name: form.name, email: form.email, phone: form.phone || undefined };
      if (editId) {
        await api.members.update(editId, payload);
      } else {
        await api.members.create(payload);
      }
      setForm({ name: "", email: "", phone: "" });
      setEditId(null);
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to save member");
    }
  };

  const startEdit = (m: Member) => {
    setEditId(m.id);
    setForm({ name: m.name, email: m.email, phone: m.phone ?? "" });
  };

  return (
    <main className="max-w-3xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Members</h1>

      {error && <p className="text-red-600 mb-4 p-2 bg-red-50 rounded">{error}</p>}

      <form onSubmit={handleSubmit} className="mb-8 p-4 border rounded bg-gray-50 space-y-3">
        <h2 className="font-semibold">{editId ? "Edit Member" : "Add Member"}</h2>
        <div className="grid grid-cols-2 gap-3">
          <input required placeholder="Name" value={form.name}
            onChange={e => setForm({ ...form, name: e.target.value })}
            className="border p-2 rounded col-span-2" />
          <input required type="email" placeholder="Email" value={form.email}
            onChange={e => setForm({ ...form, email: e.target.value })}
            className="border p-2 rounded" />
          <input placeholder="Phone (optional)" value={form.phone}
            onChange={e => setForm({ ...form, phone: e.target.value })}
            className="border p-2 rounded" />
        </div>
        <div className="flex gap-2">
          <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
            {editId ? "Update" : "Add Member"}
          </button>
          {editId && (
            <button type="button" onClick={() => { setEditId(null); setForm({ name: "", email: "", phone: "" }); }}
              className="px-4 py-2 border rounded hover:bg-gray-100">Cancel</button>
          )}
        </div>
      </form>

      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="bg-gray-100 text-left">
            <th className="border px-3 py-2">Name</th>
            <th className="border px-3 py-2">Email</th>
            <th className="border px-3 py-2">Phone</th>
            <th className="border px-3 py-2"></th>
          </tr>
        </thead>
        <tbody>
          {members.map(m => (
            <tr key={m.id} className="hover:bg-gray-50">
              <td className="border px-3 py-2">{m.name}</td>
              <td className="border px-3 py-2">{m.email}</td>
              <td className="border px-3 py-2 text-gray-500">{m.phone ?? "—"}</td>
              <td className="border px-3 py-2">
                <button onClick={() => startEdit(m)} className="text-blue-600 hover:underline text-xs">Edit</button>
              </td>
            </tr>
          ))}
          {members.length === 0 && (
            <tr><td colSpan={4} className="border px-3 py-4 text-center text-gray-400">No members found</td></tr>
          )}
        </tbody>
      </table>
    </main>
  );
}
