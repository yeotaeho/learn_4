'use client'

import { useState } from 'react'
import Chat from '@/components/Chat'

export default function Home() {
  return (
    <main style={{ width: '100%', height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <Chat />
    </main>
  )
}


