// app/layout.tsx
import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "DesignMate AI — Autonomous Interior Design",
  description: "Multi-agent AI system for intelligent interior design",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-white antialiased">
        {children}
      </body>
    </html>
  )
}