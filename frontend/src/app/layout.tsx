import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { Copilot } from "@/components/Copilot"
import { AuthGuard } from "@/components/AuthGuard"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "DClaw Crisis",
  description: "AI-native Crisis & Incident Command Center",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AuthGuard>
          {children}
          <Copilot />
        </AuthGuard>
      </body>
    </html>
  )
}
