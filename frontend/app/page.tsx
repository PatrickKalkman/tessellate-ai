'use client'

import { useState, useEffect } from 'react'
import PuzzleSelector from '@/components/PuzzleSelector'
import PuzzleBoard from '@/components/PuzzleBoard'
import { PuzzleManifest } from '@/types/puzzle'

export default function Home() {
  const [selectedPuzzle, setSelectedPuzzle] = useState<string | null>(null)
  const [manifest, setManifest] = useState<PuzzleManifest | null>(null)

  useEffect(() => {
    if (selectedPuzzle) {
      fetch(`/puzzles/${selectedPuzzle}/manifest.json`)
        .then(res => res.json())
        .then(data => setManifest(data))
        .catch(err => console.error('Error loading manifest:', err))
    }
  }, [selectedPuzzle])

  return (
    <main className="min-h-screen bg-gray-100">
      {!selectedPuzzle ? (
        <PuzzleSelector onSelect={setSelectedPuzzle} />
      ) : manifest ? (
        <PuzzleBoard 
          puzzleId={selectedPuzzle} 
          manifest={manifest} 
          onBack={() => {
            setSelectedPuzzle(null)
            setManifest(null)
          }}
        />
      ) : (
        <div className="flex items-center justify-center h-screen">
          <div className="text-xl">Loading puzzle...</div>
        </div>
      )}
    </main>
  )
}