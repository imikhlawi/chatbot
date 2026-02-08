import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PDF-Chatbot",
  description: "RAG-Chatbot für PDF-Dokumente",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="de">
      <body className="antialiased min-h-screen bg-slate-50 text-slate-900">
        {children}
      </body>
    </html>
  );
}
