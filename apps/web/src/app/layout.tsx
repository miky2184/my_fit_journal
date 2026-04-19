import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'MyFit Journal',
  description: 'Track your fitness journey',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="it">
      <body className="min-h-screen bg-gray-50 text-gray-900 antialiased">{children}</body>
    </html>
  )
}
