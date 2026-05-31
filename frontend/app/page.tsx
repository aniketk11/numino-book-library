import Link from "next/link";

export default function Home() {
  return (
    <main className="max-w-2xl mx-auto p-12 text-center">
      <h1 className="text-3xl font-bold mb-4">Neighborhood Library Service</h1>
      <p className="text-gray-500 mb-8">Manage books, members, and lending operations.</p>
      <div className="flex justify-center gap-4">
        <Link href="/books"   className="bg-blue-600 text-white px-6 py-3 rounded hover:bg-blue-700">Books</Link>
        <Link href="/members" className="bg-blue-600 text-white px-6 py-3 rounded hover:bg-blue-700">Members</Link>
        <Link href="/borrowings" className="bg-blue-600 text-white px-6 py-3 rounded hover:bg-blue-700">Borrowings</Link>
      </div>
    </main>
  );
}
