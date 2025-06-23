'use client'

import { useState, useEffect, useRef, Suspense } from 'react'
import dynamic from 'next/dynamic'
import { PuzzleManifest, PuzzleState } from '@/types/puzzle'
import type { Stage as StageType } from 'konva/lib/Stage'

const KonvaStage = dynamic(
  async () => {
    const { Stage, Layer, Image: KonvaImage } = await import('react-konva')
    const useImage = (await import('use-image')).default
    
    return function PuzzleCanvas({ puzzleId, manifest, puzzleState, handlePieceDragEnd, stageSize, stageRef, backgroundImage }: any) {
      return (
        <Stage 
          width={stageSize.width} 
          height={stageSize.height}
          ref={stageRef}
          className="mt-20"
        >
          <Layer>
            {/* Background image (faded) */}
            {backgroundImage && (
              <KonvaImage
                image={backgroundImage}
                x={(stageSize.width - manifest.size) / 2}
                y={(stageSize.height - manifest.size) / 2}
                width={manifest.size}
                height={manifest.size}
                opacity={0.2}
              />
            )}

            {/* Puzzle pieces */}
            {manifest.pieces.map((piece: any) => {
              const state = puzzleState.pieces[piece.id]
              if (!state) return null

              return (
                <PuzzlePiece
                  key={piece.id}
                  id={piece.id}
                  puzzleId={puzzleId}
                  piece={piece}
                  state={state}
                  manifest={manifest}
                  stageSize={stageSize}
                  onDragEnd={handlePieceDragEnd}
                  KonvaImage={KonvaImage}
                  useImage={useImage}
                />
              )
            })}
          </Layer>
        </Stage>
      )
    }
  },
  { ssr: false }
)

function PuzzlePiece({ id, puzzleId, piece, state, manifest, stageSize, onDragEnd, KonvaImage, useImage }: any) {
  const imageUrl = `/puzzles/${puzzleId}/piece_${id.toString().padStart(3, '0')}.png`
  const [image] = useImage(imageUrl)
  const [position, setPosition] = useState({ x: state.currentX, y: state.currentY })

  useEffect(() => {
    if (state.isPlaced) {
      setPosition({ 
        x: piece.x + (stageSize.width - manifest.size) / 2, 
        y: piece.y + (stageSize.height - manifest.size) / 2 
      })
    }
  }, [state.isPlaced, piece.x, piece.y, stageSize, manifest.size])

  return (
    <KonvaImage
      image={image}
      x={position.x}
      y={position.y}
      draggable={!state.isPlaced}
      onDragEnd={(e: any) => {
        const node = e.target
        const x = node.x()
        const y = node.y()
        setPosition({ x, y })
        onDragEnd(id, x, y)
      }}
      shadowColor="black"
      shadowBlur={state.isPlaced ? 0 : 5}
      shadowOffsetX={state.isPlaced ? 0 : 3}
      shadowOffsetY={state.isPlaced ? 0 : 3}
      shadowOpacity={state.isPlaced ? 0 : 0.3}
    />
  )
}

interface PuzzleBoardProps {
  puzzleId: string
  manifest: PuzzleManifest
  onBack: () => void
}

export default function PuzzleBoard({ puzzleId, manifest, onBack }: PuzzleBoardProps) {
  const stageRef = useRef<StageType>(null)
  const [stageSize, setStageSize] = useState({ width: 800, height: 600 })
  const [backgroundImage, setBackgroundImage] = useState<HTMLImageElement | null>(null)
  const [puzzleState, setPuzzleState] = useState<PuzzleState>(() => {
    // Load saved state from localStorage
    if (typeof window !== 'undefined') {
      const savedState = localStorage.getItem(`puzzle-${puzzleId}`)
      if (savedState) {
        return JSON.parse(savedState)
      }
    }

    // Initialize new state with random positions
    const pieces: PuzzleState['pieces'] = {}
    const margin = 150
    manifest.pieces.forEach((piece) => {
      pieces[piece.id] = {
        currentX: Math.random() * (stageSize.width - margin * 2) + margin,
        currentY: Math.random() * (stageSize.height - margin * 2) + margin,
        isPlaced: false
      }
    })
    return { pieces }
  })

  const [isCompleted, setIsCompleted] = useState(false)

  // Load background image
  useEffect(() => {
    const img = new Image()
    img.src = `/puzzles/${puzzleId}/original.jpg`
    img.onload = () => setBackgroundImage(img)
  }, [puzzleId])

  // Update stage size on mount and resize
  useEffect(() => {
    const updateSize = () => {
      setStageSize({
        width: window.innerWidth,
        height: window.innerHeight - 80 // Leave space for header
      })
    }
    updateSize()
    window.addEventListener('resize', updateSize)
    return () => window.removeEventListener('resize', updateSize)
  }, [])

  // Save state to localStorage whenever it changes
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem(`puzzle-${puzzleId}`, JSON.stringify(puzzleState))
    }
  }, [puzzleId, puzzleState])

  // Check if puzzle is completed
  useEffect(() => {
    const allPiecesPlaced = Object.values(puzzleState.pieces).every(piece => piece.isPlaced)
    if (allPiecesPlaced && manifest.pieces.length > 0) {
      setIsCompleted(true)
      setPuzzleState(prev => ({
        ...prev,
        completedAt: new Date().toISOString()
      }))
    }
  }, [puzzleState.pieces, manifest.pieces.length])

  const handlePieceDragEnd = (pieceId: number, x: number, y: number) => {
    const piece = manifest.pieces.find(p => p.id === pieceId)
    if (!piece) return

    const snapDistance = 30 // pixels
    const targetX = piece.x + (stageSize.width - manifest.size) / 2
    const targetY = piece.y + (stageSize.height - manifest.size) / 2
    
    const isSnapped = 
      Math.abs(x - targetX) < snapDistance && 
      Math.abs(y - targetY) < snapDistance

    setPuzzleState(prev => ({
      ...prev,
      pieces: {
        ...prev.pieces,
        [pieceId]: {
          currentX: isSnapped ? targetX : x,
          currentY: isSnapped ? targetY : y,
          isPlaced: isSnapped
        }
      }
    }))
  }

  const resetPuzzle = () => {
    const pieces: PuzzleState['pieces'] = {}
    const margin = 150
    manifest.pieces.forEach((piece) => {
      pieces[piece.id] = {
        currentX: Math.random() * (stageSize.width - margin * 2) + margin,
        currentY: Math.random() * (stageSize.height - margin * 2) + margin,
        isPlaced: false
      }
    })
    setPuzzleState({ pieces })
    setIsCompleted(false)
  }

  const placedCount = Object.values(puzzleState.pieces).filter(p => p.isPlaced).length
  const progress = (placedCount / manifest.pieces.length) * 100

  return (
    <div className="relative h-screen bg-gray-900">
      {/* Header */}
      <div className="absolute top-0 left-0 right-0 bg-gray-800 text-white p-4 z-10">
        <div className="container mx-auto flex items-center justify-between">
          <button
            onClick={onBack}
            className="px-4 py-2 bg-gray-700 rounded hover:bg-gray-600 transition"
          >
            Back to Puzzles
          </button>
          
          <div className="flex items-center gap-4">
            <div className="text-sm">
              Progress: {placedCount}/{manifest.pieces.length} pieces
            </div>
            <div className="w-48 bg-gray-700 rounded-full h-2">
              <div 
                className="bg-green-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
            <button
              onClick={resetPuzzle}
              className="px-4 py-2 bg-red-600 rounded hover:bg-red-700 transition"
            >
              Reset
            </button>
          </div>
        </div>
      </div>

      {/* Puzzle Stage */}
      <Suspense fallback={
        <div className="flex items-center justify-center h-screen">
          <div className="text-white text-xl">Loading puzzle...</div>
        </div>
      }>
        <KonvaStage
          puzzleId={puzzleId}
          manifest={manifest}
          puzzleState={puzzleState}
          handlePieceDragEnd={handlePieceDragEnd}
          stageSize={stageSize}
          stageRef={stageRef}
          backgroundImage={backgroundImage}
        />
      </Suspense>

      {/* Completion Modal */}
      {isCompleted && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 max-w-md text-center">
            <h2 className="text-3xl font-bold mb-4">Congratulations!</h2>
            <p className="text-xl mb-6">You completed the puzzle!</p>
            <div className="flex gap-4 justify-center">
              <button
                onClick={onBack}
                className="px-6 py-3 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
              >
                Choose Another Puzzle
              </button>
              <button
                onClick={resetPuzzle}
                className="px-6 py-3 bg-gray-600 text-white rounded hover:bg-gray-700 transition"
              >
                Play Again
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}