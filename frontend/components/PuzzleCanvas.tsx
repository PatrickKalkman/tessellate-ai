'use client'

import { Stage, Layer, Image as KonvaImage, Rect, Line, Group } from 'react-konva'
import { useImage } from './KonvaLoader'

function PuzzlePiece({ id, puzzleId, piece, state, manifest, stageSize, playAreaHeight, onDragEnd, scrollX, trayHeight, currentScrollX, scale, puzzleOffsetX, puzzleOffsetY, scaledPuzzleWidth, scaledPuzzleHeight, pieceWidth, pieceHeight, originalPieceWidth, originalPieceHeight }: any) {
  const imageUrl = `/puzzles/${puzzleId}/piece_${id.toString().padStart(3, '0')}.png`
  const [image, status] = useImage(imageUrl)
  
  // Don't render until image is loaded
  if (!image || status !== 'loaded') return null
  
  // Simple positioning - scale piece positions when placed
  const displayX = state.isPlaced 
    ? puzzleOffsetX + (piece.x * scale)
    : state.currentX
  const displayY = state.isPlaced 
    ? puzzleOffsetY + (piece.y * scale)
    : state.currentY

  // Don't render pieces that are scrolled out of view (only for pieces in tray)
  if (!state.isPlaced && !state.isOnBoard) {
    const visibleLeft = currentScrollX - 192 // Allow some buffer for dragging
    const visibleRight = currentScrollX + stageSize.width + 192
    if (state.currentX < visibleLeft || state.currentX > visibleRight) return null
  }

  return (
    <KonvaImage
      image={image}
      x={displayX}
      y={displayY}
      width={pieceWidth}
      height={pieceHeight}
      draggable={!state.isPlaced}  // Only draggable if not correctly placed
      onDragStart={() => {}}
      onDragMove={(e: any) => {
        // Just let Konva handle the drag movement
      }}
      onDragEnd={(e: any) => {
        const node = e.target
        const absolutePos = node.getAbsolutePosition()
        
        // If the piece started in the scrollable group (tray), we need to account for the group's transform
        const wasInTray = !state.isPlaced && !state.isOnBoard
        
        if (absolutePos.y < playAreaHeight) {
          // Piece is being dropped on the board
          onDragEnd(id, absolutePos.x, absolutePos.y)
        } else {
          // Piece is being dropped back in the tray
          // Need to calculate the position within the scrollable area
          const trayX = absolutePos.x + currentScrollX
          onDragEnd(id, trayX, absolutePos.y)
        }
      }}
      shadowColor="black"
      shadowBlur={state.isPlaced ? 0 : 5}
      shadowOffsetX={state.isPlaced ? 0 : 3}
      shadowOffsetY={state.isPlaced ? 0 : 3}
      shadowOpacity={state.isPlaced ? 0 : 0.3}
    />
  )
}

export default function PuzzleCanvas({ puzzleId, manifest, puzzleState, handlePieceDragEnd, stageSize, stageRef, backgroundImage, trayHeight, scrollX, setCurrentScrollX, trayPaddingTop, currentScrollX, pieceWidth, pieceHeight, originalPieceWidth, originalPieceHeight, pieceSpacing, scale, puzzleOffsetX, puzzleOffsetY, scaledPuzzleWidth, scaledPuzzleHeight, bgX, bgY, bgWidth, bgHeight, showBackground }: any) {
  const playAreaHeight = stageSize.height - trayHeight
  
  return (
    <Stage 
      width={stageSize.width} 
      height={stageSize.height}
      ref={stageRef}
      className=""
      onWheel={(e: any) => {
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
        
        {/* Background image (faded or full based on showBackground) */}
        {backgroundImage && (
          <KonvaImage
            image={backgroundImage}
            x={bgX}
            y={bgY}
            width={bgWidth}
            height={bgHeight}
            opacity={showBackground ? 1.0 : 0.2}
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
                scrollX={scrollX}
                trayHeight={trayHeight}
                currentScrollX={currentScrollX}
                scale={scale}
                puzzleOffsetX={puzzleOffsetX}
                puzzleOffsetY={puzzleOffsetY}
                scaledPuzzleWidth={scaledPuzzleWidth}
                scaledPuzzleHeight={scaledPuzzleHeight}
                pieceWidth={pieceWidth}
                pieceHeight={pieceHeight}
                originalPieceWidth={originalPieceWidth}
                originalPieceHeight={originalPieceHeight}
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
              scrollX={scrollX}
              trayHeight={trayHeight}
              currentScrollX={currentScrollX}
              scale={scale}
              puzzleOffsetX={puzzleOffsetX}
              puzzleOffsetY={puzzleOffsetY}
              pieceWidth={pieceWidth}
              pieceHeight={pieceHeight}
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
              scrollX={scrollX}
              trayHeight={trayHeight}
              currentScrollX={currentScrollX}
              scale={scale}
              puzzleOffsetX={puzzleOffsetX}
              puzzleOffsetY={puzzleOffsetY}
              scaledPuzzleWidth={scaledPuzzleWidth}
              scaledPuzzleHeight={scaledPuzzleHeight}
              pieceWidth={pieceWidth}
              pieceHeight={pieceHeight}
              originalPieceWidth={originalPieceWidth}
              originalPieceHeight={originalPieceHeight}
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