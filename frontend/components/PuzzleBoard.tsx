'use client'

import { useState, useEffect, useRef, Suspense } from 'react'
import dynamic from 'next/dynamic'
import { PuzzleManifest, PuzzleState } from '@/types/puzzle'
import type { Stage as StageType } from 'konva/lib/Stage'

const KonvaStage = dynamic(
  async () => {
    const { Stage, Layer, Image: KonvaImage, Rect, Line, Group } = await import('react-konva')
    const useImage = (await import('use-image')).default
    
    return function PuzzleCanvas({ puzzleId, manifest, puzzleState, handlePieceDragEnd, stageSize, stageRef, backgroundImage, trayHeight, scrollX, setCurrentScrollX, trayPaddingTop, currentScrollX, basePieceSize, pieceSpacing, scale, puzzleOffsetX, puzzleOffsetY, scaledPuzzleWidth, scaledPuzzleHeight, bgX, bgY, bgWidth, bgHeight }: any) {
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
              const newScrollX = Math.max(0, scrollX.current + delta)
              scrollX.current = newScrollX
              setCurrentScrollX(newScrollX)
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
                x={bgX}
                y={bgY}
                width={bgWidth}
                height={bgHeight}
                opacity={0.2}
              />
            )}

            {/* Tray area background - fixed position */}
            <Rect
              x={0}
              y={playAreaHeight}
              width={stageSize.width}
              height={trayHeight}
              fill="#2a2a2a"
            />
            
            {/* Separator line - fixed position */}
            <Line
              points={[0, playAreaHeight, stageSize.width, playAreaHeight]}
              stroke="#444"
              strokeWidth={2}
            />

            {/* Unplaced pieces in tray - wrapped in a scrollable group */}
            <Group x={-currentScrollX} y={0} draggable={false}>
              {[...manifest.pieces].sort((a, b) => a.id - b.id).map((piece: any) => {
                const state = puzzleState.pieces[piece.id]
                if (!state || state.isPlaced || state.isOnBoard) return null

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
                    currentScrollX={currentScrollX}
                    Rect={Rect}
                    scale={scale}
                    puzzleOffsetX={puzzleOffsetX}
                    puzzleOffsetY={puzzleOffsetY}
                    scaledPuzzleWidth={scaledPuzzleWidth}
                    scaledPuzzleHeight={scaledPuzzleHeight}
                  />
                )
              })}
            </Group>

            {/* Pieces on board but not correctly placed (not affected by scroll) */}
            {[...manifest.pieces].sort((a, b) => a.id - b.id).map((piece: any) => {
              const state = puzzleState.pieces[piece.id]
              if (!state || state.isPlaced || !state.isOnBoard) return null

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
                  currentScrollX={currentScrollX}
                  Rect={Rect}
                  scale={scale}
                  puzzleOffsetX={puzzleOffsetX}
                  puzzleOffsetY={puzzleOffsetY}
                />
              )
            })}

            {/* Correctly placed pieces (not affected by scroll) - rendered AFTER tray elements */}
            {[...manifest.pieces].sort((a, b) => a.id - b.id).map((piece: any) => {
              const state = puzzleState.pieces[piece.id]
              if (!state || !state.isPlaced) return null

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
                  currentScrollX={currentScrollX}
                  Rect={Rect}
                  scale={scale}
                  puzzleOffsetX={puzzleOffsetX}
                  puzzleOffsetY={puzzleOffsetY}
                  scaledPuzzleWidth={scaledPuzzleWidth}
                  scaledPuzzleHeight={scaledPuzzleHeight}
                />
              )
            })}
            
            {/* Scroll indicators */}
            {currentScrollX > 0 && (
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

function PuzzlePiece({ id, puzzleId, piece, state, manifest, stageSize, playAreaHeight, onDragEnd, KonvaImage, useImage, scrollX, trayHeight, currentScrollX, Rect, scale, puzzleOffsetX, puzzleOffsetY, scaledPuzzleWidth, scaledPuzzleHeight }: any) {
  const basePieceSize = 192 // Original size of the puzzle grid square
  const tabSize = pieceSize / 4
  const fullPieceSize = pieceSize + tabSize * 2 in the puzzle grid
  const imageUrl = `/puzzles/${puzzleId}/piece_${id.toString().padStart(3, '0')}.png`
  const [image] = useImage(imageUrl)
  const [isDragging, setIsDragging] = useState(false)
  
  

  // For pieces on the board (placed or not), use the stored position directly
  // This prevents recalculation when stageSize changes
  // For correctly placed pieces, just scale the coordinates directly
  const displayX = state.isPlaced 
    ? puzzleOffsetX + (piece.x * scale)
    : (state.isOnBoard ? state.currentX : state.currentX)
  const displayY = state.isPlaced 
    ? puzzleOffsetY + (piece.y * scale)
    : (state.isOnBoard ? state.currentY : state.currentY)




  // Don't render pieces that are scrolled out of view (only for pieces in tray)
  if (!state.isPlaced && !state.isOnBoard) {
    const visibleLeft = currentScrollX - 192 // Allow some buffer for dragging
    const visibleRight = currentScrollX + stageSize.width + 192
    if (state.currentX < visibleLeft || state.currentX > visibleRight) return null
  }

  // Always scale pieces consistently
  const currentScale = scale
  
  return (
    <KonvaImage
      image={image}
      x={displayX}
      y={displayY}
      width={basePieceSize * currentScale}
      height={basePieceSize * currentScale}
      draggable={!state.isPlaced}  // Only draggable if not correctly placed
      onDragStart={() => setIsDragging(true)}
      onDragMove={(e: any) => {
        // Just let Konva handle the drag movement
      }}
      onDragEnd={(e: any) => {
        const node = e.target
        const absolutePos = node.getAbsolutePosition()
        
        // Get the position relative to the stage
        const stagePos = node.getPosition()
        
        // If the piece started in the scrollable group (tray), we need to account for the group's transform
        const wasInTray = !state.isPlaced && !state.isOnBoard
        
        if (absolutePos.y < playAreaHeight) {
          // Piece is being dropped on the board
          if (wasInTray) {
            // Coming from tray - need to account for the group's x offset
            onDragEnd(id, absolutePos.x, absolutePos.y)
          } else {
            // Already on board - use position directly
            onDragEnd(id, absolutePos.x, absolutePos.y)
          }
        } else {
          // Piece is being dropped back in the tray
          // Need to calculate the position within the scrollable area
          const trayX = absolutePos.x + currentScrollX
          onDragEnd(id, trayX, absolutePos.y)
        }
        
        setIsDragging(false)
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
  const [backgroundDimensions, setBackgroundDimensions] = useState<{width: number, height: number} | null>(null)
  const basePieceSize = 192 // Original size of each piece in the puzzle grid
  const pieceSpacing = 20 // Spacing between pieces in tray
  const trayPaddingTop = 16 // Top padding for pieces in tray
  const scrollX = useRef(0)
  const [, forceUpdate] = useState({})
  const [currentScrollX, setCurrentScrollX] = useState(0)
  
  // Calculate scale to fit puzzle in available space
  const trayHeight = 160 // Fixed tray height
  const playAreaHeight = stageSize.height - trayHeight
  const padding = 40 // Padding around the puzzle
  const maxPuzzleWidth = stageSize.width - padding * 2
  const maxPuzzleHeight = playAreaHeight - padding * 2
  const puzzleWidth = manifest.width || manifest.size || 2048
  const puzzleHeight = manifest.height || manifest.size || 2048
  const scaleX = Math.min(maxPuzzleWidth / puzzleWidth, 1)
  const scaleY = Math.min(maxPuzzleHeight / puzzleHeight, 1)
  const scale = Math.min(scaleX, scaleY)
  
  const scaledPuzzleWidth = puzzleWidth * scale
  const scaledPuzzleHeight = puzzleHeight * scale
  const puzzleOffsetX = (stageSize.width - scaledPuzzleWidth) / 2
  const puzzleOffsetY = (playAreaHeight - scaledPuzzleHeight) / 2
  
  // Calculate background image dimensions preserving aspect ratio
  let bgWidth = scaledPuzzleWidth
  let bgHeight = scaledPuzzleHeight
  let bgX = puzzleOffsetX
  let bgY = puzzleOffsetY
  
  if (backgroundDimensions) {
    const bgAspectRatio = backgroundDimensions.width / backgroundDimensions.height
    const puzzleAspectRatio = 1 // Puzzle is square
    
    if (bgAspectRatio > puzzleAspectRatio) {
      // Background is wider than puzzle (e.g., 16:9)
      bgWidth = scaledPuzzleWidth
      bgHeight = scaledPuzzleWidth / bgAspectRatio
      bgY = puzzleOffsetY + (scaledPuzzleHeight - bgHeight) / 2
    } else {
      // Background is taller than puzzle
      bgHeight = scaledPuzzleHeight
      bgWidth = scaledPuzzleHeight * bgAspectRatio
      bgX = puzzleOffsetX + (scaledPuzzleWidth - bgWidth) / 2
    }
  }
  
  const [puzzleState, setPuzzleState] = useState<PuzzleState>(() => {
    // Load saved state from localStorage
    if (typeof window !== 'undefined') {
      const savedState = localStorage.getItem(`puzzle-${puzzleId}`)
      if (savedState) {
        const parsed = JSON.parse(savedState)
        // Recalculate positions for unplaced pieces
        const initialHeight = window.innerHeight - 80
        const initialY = initialHeight - trayHeight + trayPaddingTop
        
        // Sort pieces by ID and reset positions
        const sortedPieces = [...manifest.pieces].sort((a, b) => a.id - b.id)
        let trayIndex = 0
        
        sortedPieces.forEach((manifestPiece) => {
          const savedPiece = parsed.pieces[manifestPiece.id]
          if (savedPiece) {
            if (savedPiece.isPlaced) {
              // For placed pieces, keep them at their correct positions
              // These will be recalculated based on current scale
            } else if (savedPiece.isOnBoard) {
              // For pieces on board but not placed, keep their relative positions
              // Don't change their positions as they should maintain board placement
            } else {
              // For pieces in tray, reset to sequential positions
              savedPiece.currentX = pieceSpacing + (trayIndex * (basePieceSize * scale + pieceSpacing))
              savedPiece.currentY = initialY
              savedPiece.isOnBoard = false
              trayIndex++
            }
          }
        })
        
        return parsed
      }
    }

    // Initialize new state with pieces in the tray
    const pieces: PuzzleState['pieces'] = {}
    
    // Sort pieces by ID to ensure sequential layout
    const sortedPieces = [...manifest.pieces].sort((a, b) => a.id - b.id)
    
    // Calculate initial Y position based on window height
    const initialHeight = typeof window !== 'undefined' ? window.innerHeight - 80 : 600
    const initialY = initialHeight - trayHeight + trayPaddingTop
    
    sortedPieces.forEach((piece, index) => {
      const trayX = pieceSpacing + (index * (basePieceSize * scale + pieceSpacing))
      pieces[piece.id] = {
        currentX: trayX,
        currentY: initialY,
        isPlaced: false,
        isOnBoard: false
      }
    })
    return { pieces }
  })

  const [isCompleted, setIsCompleted] = useState(false)

  // Load background image
  useEffect(() => {
    const img = new Image()
    img.src = `/puzzles/${puzzleId}/original.jpg`
    img.onload = () => {
      setBackgroundImage(img)
      setBackgroundDimensions({
        width: img.naturalWidth,
        height: img.naturalHeight
      })
    }
  }, [puzzleId])

  // Update stage size on mount and resize
  useEffect(() => {
    const updateSize = () => {
      const newHeight = window.innerHeight - 80 // Leave space for header
      setStageSize({
        width: window.innerWidth,
        height: newHeight
      })
      
      // Update Y position for unplaced pieces when stage size changes
      setPuzzleState(prev => {
        const updatedPieces = { ...prev.pieces }
        let hasUpdates = false
        const newY = newHeight - trayHeight + trayPaddingTop
        
        Object.keys(updatedPieces).forEach(id => {
          const piece = updatedPieces[parseInt(id)]
          // Only update if piece is in tray (not placed AND not on board) and Y position changed significantly
          if (!piece.isPlaced && !piece.isOnBoard && Math.abs(piece.currentY - newY) > 5) {
            piece.currentY = newY
            hasUpdates = true
          }
        })
        return hasUpdates ? { ...prev, pieces: updatedPieces } : prev
      })
    }
    updateSize()
    window.addEventListener('resize', updateSize)
    return () => window.removeEventListener('resize', updateSize)
  }, [trayHeight, trayPaddingTop])

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

  // Removed window wheel event listener - using Stage onWheel instead to avoid conflicts

  const handlePieceDragEnd = (pieceId: number, x: number, y: number) => {
    const piece = manifest.pieces.find(p => p.id === pieceId)
    if (!piece) return

    const playAreaHeight = stageSize.height - trayHeight
    const snapDistance = 40 * scale // Increased snap distance for easier placement
    const adjacentSnapDistance = 30 * scale // Distance for snapping to adjacent pieces
    const targetX = puzzleOffsetX + (piece.x * scale)
    const targetY = puzzleOffsetY + (piece.y * scale)
    
    // Check if piece is on the board (not in tray)
    const isOnBoard = y < playAreaHeight
    
    // Check if piece is snapped to correct position
    let isSnapped = 
      Math.abs(x - targetX) < snapDistance && 
      Math.abs(y - targetY) < snapDistance &&
      isOnBoard
    
    let finalX = x
    let finalY = y
    
    // If not snapped to correct position, check for adjacent piece snapping
    if (!isSnapped && isOnBoard) {
      // Find the piece's neighbors in the grid
      const row = Math.floor(piece.y / 128)
      const col = Math.floor(piece.x / 128)
      
      // Calculate max rows and cols based on puzzle dimensions
      const totalCols = Math.ceil(puzzleWidth / 128)
      const totalRows = Math.ceil(puzzleHeight / 128)
      
      // Check all four directions for placed pieces
      const neighbors = [
        { row: row - 1, col: col, dRow: -1, dCol: 0 }, // top
        { row: row + 1, col: col, dRow: 1, dCol: 0 },  // bottom
        { row: row, col: col - 1, dRow: 0, dCol: -1 }, // left
        { row: row, col: col + 1, dRow: 0, dCol: 1 }   // right
      ]
      
      for (const neighbor of neighbors) {
        if (neighbor.row >= 0 && neighbor.row < totalRows && neighbor.col >= 0 && neighbor.col < totalCols) {
          // Find the neighbor piece
          const neighborPiece = manifest.pieces.find(p => 
            Math.floor(p.y / 128) === neighbor.row && 
            Math.floor(p.x / 128) === neighbor.col
          )
          
          if (neighborPiece) {
            const neighborState = puzzleState.pieces[neighborPiece.id]
            
            // If neighbor is placed, check if we can snap to it
            if (neighborState && neighborState.isPlaced) {
              // For placed pieces, currentX/Y are the actual target positions
              // So we calculate the expected position based on the original grid positions
              const expectedX = puzzleOffsetX + ((piece.x + neighbor.dCol * 128) * scale)
              const expectedY = puzzleOffsetY + ((piece.y + neighbor.dRow * 128) * scale)
              
              if (Math.abs(x - expectedX) < adjacentSnapDistance && 
                  Math.abs(y - expectedY) < adjacentSnapDistance) {
                // Snap to the adjacent piece position
                finalX = expectedX
                finalY = expectedY
                
                // Check if this also happens to be the correct position
                isSnapped = Math.abs(finalX - targetX) < 1 && Math.abs(finalY - targetY) < 1
                break
              }
            }
          }
        }
      }
    }
    
    // Debug logging
    if (isOnBoard) {
      console.log(`Piece ${pieceId}: x=${x.toFixed(0)}, y=${y.toFixed(0)}, finalX=${finalX.toFixed(0)}, finalY=${finalY.toFixed(0)}, isSnapped=${isSnapped}`)
    }

    setPuzzleState(prev => {
      const updatedState = {
        ...prev,
        pieces: {
          ...prev.pieces,
          [pieceId]: {
            currentX: isSnapped ? targetX : finalX,
            currentY: isSnapped ? targetY : finalY,
            isPlaced: isSnapped,
            isOnBoard: isOnBoard  // New field to track if piece is on board
          }
        }
      }
      
      // Save state to localStorage
      localStorage.setItem(`puzzle-${puzzleId}`, JSON.stringify(updatedState))
      
      return updatedState
    })
  }

  const resetPuzzle = () => {
    const pieces: PuzzleState['pieces'] = {}
    
    // Sort pieces by ID to ensure sequential layout
    const sortedPieces = [...manifest.pieces].sort((a, b) => a.id - b.id)
    
    sortedPieces.forEach((piece, index) => {
      const trayX = pieceSpacing + (index * (basePieceSize * scale + pieceSpacing))
      pieces[piece.id] = {
        currentX: trayX,
        currentY: stageSize.height - trayHeight + trayPaddingTop,
        isPlaced: false,
        isOnBoard: false
      }
    })
    setPuzzleState({ pieces })
    setIsCompleted(false)
    scrollX.current = 0
    setCurrentScrollX(0)
    
    // Clear localStorage
    if (typeof window !== 'undefined') {
      localStorage.removeItem(`puzzle-${puzzleId}`)
    }
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
          setCurrentScrollX={setCurrentScrollX}
          trayPaddingTop={trayPaddingTop}
          currentScrollX={currentScrollX}
          basePieceSize={basePieceSize}
          pieceSpacing={pieceSpacing}
          scale={scale}
          puzzleOffsetX={puzzleOffsetX}
          puzzleOffsetY={puzzleOffsetY}
          scaledPuzzleWidth={scaledPuzzleWidth}
          scaledPuzzleHeight={scaledPuzzleHeight}
          bgX={bgX}
          bgY={bgY}
          bgWidth={bgWidth}
          bgHeight={bgHeight}
        />
      </Suspense>

      {/* Scroll buttons */}
      <button
        onClick={() => {
          scrollX.current = Math.max(0, scrollX.current - 200)
          setCurrentScrollX(scrollX.current)
        }}
        className={`absolute left-4 transform -translate-y-1/2 bg-gray-800 hover:bg-gray-700 text-white p-3 rounded-full transition ${currentScrollX <= 0 ? 'opacity-50 cursor-not-allowed' : ''}`}
        style={{ bottom: `${trayHeight/2}px` }}
        disabled={currentScrollX <= 0}
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polyline points="15 18 9 12 15 6"></polyline>
        </svg>
      </button>
      
      <button
        onClick={() => {
          const maxScroll = Math.max(0, manifest.pieces.length * (basePieceSize * scale + pieceSpacing) - stageSize.width + pieceSpacing * 2)
          scrollX.current = Math.min(maxScroll, scrollX.current + 200)
          setCurrentScrollX(scrollX.current)
        }}
        className={`absolute right-4 transform -translate-y-1/2 bg-gray-800 hover:bg-gray-700 text-white p-3 rounded-full transition ${currentScrollX >= Math.max(0, manifest.pieces.length * (basePieceSize * scale + pieceSpacing) - stageSize.width + pieceSpacing * 2) ? 'opacity-50 cursor-not-allowed' : ''}`}
        style={{ bottom: `${trayHeight/2}px` }}
        disabled={currentScrollX >= Math.max(0, manifest.pieces.length * (basePieceSize * scale + pieceSpacing) - stageSize.width + pieceSpacing * 2)}
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polyline points="9 18 15 12 9 6"></polyline>
        </svg>
      </button>

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