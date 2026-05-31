import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Neighborhood Library",
  description: "Library management service",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="h-full" style={{ colorScheme: "light" }}>
      <body className="min-h-full flex flex-col bg-white text-gray-900">
        <nav className="bg-blue-700 text-white px-6 py-3 flex gap-6 items-center">
          <span className="font-bold text-lg mr-4">📚 Library</span>
          <Link href="/books"   className="hover:underline">Books</Link>
          <Link href="/members" className="hover:underline">Members</Link>
          <Link href="/borrowings" className="hover:underline">Borrowings</Link>
        </nav>
        <div className="flex-1">{children}</div>
      </body>
    </html>
  );
}
