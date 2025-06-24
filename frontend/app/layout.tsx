import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { KonvaScripts } from '@/components/KonvaLoader'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Tessellate AI - Digital Jigsaw Puzzles',
  description: 'AI-generated jigsaw puzzles for endless entertainment',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        {children}
        <KonvaScripts />
      </body>
    </html>
  )
}