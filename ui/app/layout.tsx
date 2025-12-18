import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'LangChain RAG Chatbot',
  description: 'RAG 방식의 챗봇 애플리케이션',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  )
}


