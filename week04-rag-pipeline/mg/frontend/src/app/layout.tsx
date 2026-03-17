import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RAG Pipeline",
  description: "4주차 과제 — 기본 RAG 파이프라인 & 챗봇 데모",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;1,300&family=Outfit:wght@300;400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-base font-sans text-pearl antialiased">
        {children}
      </body>
    </html>
  );
}
