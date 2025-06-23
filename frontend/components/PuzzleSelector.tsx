import { useState, useEffect } from 'react'
import Image from 'next/image'

interface PuzzleInfo {
  id: string
  thumbnailUrl: string
  metadata?: {
    prompt: string
    quality_score: number
    generation_time: string
  }
}

interface PuzzleSelectorProps {
  onSelect: (puzzleId: string) => void
}

export default function PuzzleSelector({ onSelect }: PuzzleSelectorProps) {
  const [puzzles, setPuzzles] = useState<PuzzleInfo[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // For now, manually check for available puzzles
    // In production, this would come from an API
    const loadPuzzles = async () => {
      const availablePuzzles: PuzzleInfo[] = []
      
      // Check first 10 puzzle IDs
      for (let i = 0; i < 10; i++) {
        const id = i.toString().padStart(4, '0')
        try {
          const response = await fetch(`/puzzles/${id}/metadata.json`)
          if (response.ok) {
            const metadata = await response.json()
            availablePuzzles.push({
              id,
              thumbnailUrl: `/puzzles/${id}/original.jpg`,
              metadata
            })
          }
        } catch (err) {
          // Puzzle doesn't exist, continue
        }
      }
      
      setPuzzles(availablePuzzles)
      setLoading(false)
    }

    loadPuzzles()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl">Loading puzzles...</div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-4xl font-bold text-center mb-8">Choose a Puzzle</h1>
      
      {puzzles.length === 0 ? (
        <div className="text-center text-gray-600">
          <p className="mb-4">No puzzles available yet.</p>
          <p>Generate puzzles using the backend command:</p>
          <pre className="bg-gray-100 p-4 rounded mt-2 inline-block">
            <code>python -m backend --count 10</code>
          </pre>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {puzzles.map((puzzle) => (
            <div
              key={puzzle.id}
              className="bg-white rounded-lg shadow-lg overflow-hidden cursor-pointer transform transition hover:scale-105"
              onClick={() => onSelect(puzzle.id)}
            >
              <div className="relative h-64">
                <Image
                  src={puzzle.thumbnailUrl}
                  alt={`Puzzle ${puzzle.id}`}
                  fill
                  className="object-cover"
                  unoptimized
                />
              </div>
              <div className="p-4">
                <h3 className="font-semibold text-lg mb-2">Puzzle #{puzzle.id}</h3>
                {puzzle.metadata && (
                  <>
                    <p className="text-sm text-gray-600 mb-1">
                      Quality Score: {puzzle.metadata.quality_score.toFixed(1)}
                    </p>
                    <p className="text-sm text-gray-600 line-clamp-2">
                      {puzzle.metadata.prompt}
                    </p>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}