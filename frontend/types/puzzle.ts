export interface PuzzlePiece {
  id: number
  x: number
  y: number
}

export interface PuzzleManifest {
  size?: number
  width: number
  height: number
  grid: [number, number]
  pieces: PuzzlePiece[]
}

export interface PuzzleMetadata {
  prompt: string
  quality_score: number
  generation_time: string
  complexity: number
}

export interface PuzzleState {
  pieces: {
    [id: number]: {
      currentX: number
      currentY: number
      isPlaced: boolean
      isOnBoard?: boolean  // Track if piece is on board but not necessarily in correct position
    }
  }
  completedAt?: string
}