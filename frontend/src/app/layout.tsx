import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ClaimEasy",
  description: "On-chain shipping damage compensation powered by GenLayer.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
