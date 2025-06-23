'use client'

import { useState, useEffect, useRef, Suspense } from 'react'
import dynamic from 'next/dynamic'
import { PuzzleManifest, PuzzleState } from '@/types/puzzle'
import type { Stage as StageType } from 'konva/lib/Stage'

const KonvaStage = dynamic(
  async () => {
    const { Stage, Layer, Image: KonvaImage, Rect, Line, Group } = await import('react-konva')
    const useImage = (await import('use-image')).default
    
    return function PuzzleCanvas({ puzzleId, manifest, puzzleState, handlePieceDragEnd, stageSize, stageRef, backgroundImage, trayHeight, scrollX }: any) {
      const playAreaHeight = stageSize.height - trayHeight
      
      return (
        <Stage 
          width={stageSize.width} 
          height={stageSize.height}
          ref={stageRef}
          className="mt-20"
          onWheel={(e) => {
            const evt = e.evt
            // Check if mouse is in tray area
            if (evt.offsetY > playAreaHeight) {
              evt.preventDefault()
              const delta = evt.deltaX || evt.deltaY
              scrollX.current = Math.max(0, scrollX.current + delta)
            }
          }}
        >
          <Layer>
            {/* Play area background */}
            <Rect
              x={0}
              y={0}
              width={stageSize.width}
              height={playAreaHeight}
              fill="#1a1a1a"
            />
            
            {/* Background image (faded) */}
            {backgroundImage && (
              <KonvaImage
                image={backgroundImage}
                x={(stageSize.width - manifest.size) / 2}
                y={(playAreaHeight - manifest.size) / 2}
                width={manifest.size}
                height={manifest.size}
                opacity={0.2}
              />
            )}

            {/* Tray area background */}
            <Rect
              x={0}
              y={playAreaHeight}
              width={stageSize.width}
              height={trayHeight}
              fill="#2a2a2a"
            />
            
            {/* Separator line */}
            <Line
              points={[0, playAreaHeight, stageSize.width, playAreaHeight]}
              stroke="#444"
              strokeWidth={2}
            />

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
                  playAreaHeight={playAreaHeight}
                  onDragEnd={handlePieceDragEnd}
                  KonvaImage={KonvaImage}
                  useImage={useImage}
                  scrollX={scrollX}
                  trayHeight={trayHeight}
                />
              )
            })}
            
            {/* Scroll indicators */}
            {scrollX.current > 0 && (
              <Group>
                <Rect
                  x={0}
                  y={playAreaHeight}
                  width={40}
                  height={trayHeight}
                  fill="rgba(0,0,0,0.5)"
                />
                <Line
                  points={[25, playAreaHeight + trayHeight/2 - 10, 15, playAreaHeight + trayHeight/2, 25, playAreaHeight + trayHeight/2 + 10]}
                  stroke="white"
                  strokeWidth={2}
                />
              </Group>
            )}
          </Layer>
        </Stage>
      )
    }
  },
  { ssr: false }
)

function PuzzlePiece({ id, puzzleId, piece, state, manifest, stageSize, playAreaHeight, onDragEnd, KonvaImage, useImage, scrollX, trayHeight }: any) {
  const imageUrl = `/puzzles/${puzzleId}/piece_${id.toString().padStart(3, '0')}.png`
  const [image] = useImage(imageUrl)
  const [position, setPosition] = useState({ x: state.currentX, y: state.currentY })
  const [isDragging, setIsDragging] = useState(false)

  useEffect(() => {
    if (state.isPlaced) {
      setPosition({ 
        x: piece.x + (stageSize.width - manifest.size) / 2, 
        y: piece.y + (playAreaHeight - manifest.size) / 2 
      })
    } else if (!isDragging) {
      // Update position for pieces in tray when scrolling
      setPosition({
        x: state.currentX - scrollX.current,
        y: state.currentY
      })
    }
  }, [state.isPlaced, state.currentX, state.currentY, piece.x, piece.y, stageSize.width, playAreaHeight, manifest.size, scrollX.current, isDragging])

  // Don't render pieces that are scrolled out of view
  if (!state.isPlaced && position.x + 128 < 0) return null
  if (!state.isPlaced && position.x > stageSize.width) return null

  return (
    <KonvaImage
      image={image}
      x={position.x}
      y={position.y}
      draggable={!state.isPlaced}
      onDragStart={() => setIsDragging(true)}
      onDragEnd={(e: any) => {
        const node = e.target
        const x = node.x()
        const y = node.y()
        setPosition({ x, y })
        setIsDragging(false)
        
        // Adjust x position for scroll when saving
        const adjustedX = y > playAreaHeight ? x + scrollX.current : x
        onDragEnd(id, adjustedX, y)
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
  const trayHeight = 200 // Height of the piece tray
  const pieceSize = 128 // Size of each piece
  const pieceSpacing = 20 // Spacing between pieces in tray
  const scrollX = useRef(0)
  const [, forceUpdate] = useState({})
  
  const [puzzleState, setPuzzleState] = useState<PuzzleState>(() => {
    // Load saved state from localStorage
    if (typeof window !== 'undefined') {
      const savedState = localStorage.getItem(`puzzle-${puzzleId}`)
      if (savedState) {
        return JSON.parse(savedState)
      }
    }

    // Initialize new state with pieces in the tray
    const pieces: PuzzleState['pieces'] = {}
    let trayX = pieceSpacing
    
    manifest.pieces.forEach((piece, index) => {
      pieces[piece.id] = {
        currentX: trayX,
        currentY: stageSize.height - trayHeight + pieceSpacing,
        isPlaced: false
      }
      trayX += pieceSize + pieceSpacing
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

  // Handle mouse wheel scrolling in tray
  useEffect(() => {
    const handleWheel = (e: WheelEvent) => {
      if (e.offsetY > stageSize.height - trayHeight) {
        e.preventDefault()
        const delta = e.deltaX || e.deltaY
        scrollX.current = Math.max(0, scrollX.current + delta)
        forceUpdate({})
      }
    }

    window.addEventListener('wheel', handleWheel, { passive: false })
    return () => window.removeEventListener('wheel', handleWheel)
  }, [stageSize.height, trayHeight])

  const handlePieceDragEnd = (pieceId: number, x: number, y: number) => {
    const piece = manifest.pieces.find(p => p.id === pieceId)
    if (!piece) return

    const playAreaHeight = stageSize.height - trayHeight
    const snapDistance = 30 // pixels
    const targetX = piece.x + (stageSize.width - manifest.size) / 2
    const targetY = piece.y + (playAreaHeight - manifest.size) / 2
    
    const isSnapped = 
      Math.abs(x - targetX) < snapDistance && 
      Math.abs(y - targetY) < snapDistance &&
      y < playAreaHeight // Must be in play area

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
    let trayX = pieceSpacing
    
    manifest.pieces.forEach((piece) => {
      pieces[piece.id] = {
        currentX: trayX,
        currentY: stageSize.height - trayHeight + pieceSpacing,
        isPlaced: false
      }
      trayX += pieceSize + pieceSpacing
    })
    setPuzzleState({ pieces })
    setIsCompleted(false)
    scrollX.current = 0
  }

  const placedCount = Object.values(puzzleState.pieces).filter(p => p.isPlaced).length
  const progress = (placedCount / manifest.pieces.length) * 100

  return (
    <div className="relative h-screen bg-gray-900 overflow-hidden">
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
          trayHeight={trayHeight}
          scrollX={scrollX}
        />
      </Suspense>

      {/* Scroll hint */}
      <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 text-white text-sm opacity-70 pointer-events-none">
        Scroll horizontally in the tray to see more pieces
      </div>

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