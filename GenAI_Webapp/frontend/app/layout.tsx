import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Local Language Summary",
  description: "Summarise, translate, and listen to text or audio in a local language."
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
