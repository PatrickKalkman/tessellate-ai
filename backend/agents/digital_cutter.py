import logging
import random
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np
from PIL import Image, ImageDraw
import svgwrite
import json

from ..core.models import PuzzlePiece, PuzzleManifest, CuttingStyle
from ..core.config import settings
from ..core.utils import (
    ensure_directory, save_json, load_image, save_image,
    calculate_piece_position, format_puzzle_id
)


logger = logging.getLogger(__name__)


class DigitalCutter:
    """Agent responsible for cutting images into jigsaw puzzle pieces"""
    
    def __init__(self, grid_size: Optional[Tuple[int, int]] = None):
        self.rows, self.cols = grid_size or settings.grid_size
        self.piece_size = settings.piece_size
        self.image_size = settings.image_size
        
        # Tab/blank parameters for classic jigsaw pieces
        self.tab_size = self.piece_size // 4  # Size of tabs/blanks
        self.tab_variation = 0.2  # Random variation in tab position
        
    def cut_puzzle(self, image_path: str, output_dir: str, 
                   style: CuttingStyle = CuttingStyle.CLASSIC) -> PuzzleManifest:
        """
        Generate all puzzle pieces from an image.
        
        Args:
            image_path: Path to the source image
            output_dir: Directory to save puzzle pieces
            style: Cutting style to use
            
        Returns:
            PuzzleManifest with piece information
        """
        logger.info(f"Cutting puzzle from {image_path} with style {style}")
        
        # Ensure output directory exists
        output_path = ensure_directory(output_dir)
        
        # Load and validate image
        image = load_image(image_path)
        if image.size != (self.image_size, self.image_size):
            logger.warning(f"Resizing image from {image.size} to ({self.image_size}, {self.image_size})")
            image = image.resize((self.image_size, self.image_size), Image.Resampling.LANCZOS)
        
        # Convert to RGBA for transparency support
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # Generate edge patterns for all pieces
        edge_patterns = self._generate_edge_patterns()
        
        # Cut pieces
        pieces = []
        piece_index = 0
        
        for row in range(self.rows):
            for col in range(self.cols):
                # Generate piece mask
                mask = self._create_piece_mask(row, col, edge_patterns, style)
                
                # Extract piece from image
                piece_image = self._extract_piece(image, row, col, mask)
                
                # Save piece
                piece_filename = f"piece_{piece_index:03d}.png"
                piece_path = output_path / piece_filename
                save_image(piece_image, piece_path)
                
                # Calculate piece position in original image
                x, y = calculate_piece_position(piece_index, self.cols, self.piece_size)
                
                pieces.append(PuzzlePiece(id=piece_index, x=x, y=y))
                piece_index += 1
        
        # Create manifest
        manifest = PuzzleManifest(
            size=self.image_size,
            grid=(self.rows, self.cols),
            pieces=pieces
        )
        
        # Save manifest
        manifest_path = output_path / "manifest.json"
        save_json(manifest.to_json_dict(), manifest_path)
        
        logger.info(f"Successfully cut {len(pieces)} puzzle pieces")
        return manifest
    
    def _generate_edge_patterns(self) -> dict:
        """
        Generate random edge patterns for all pieces.
        Returns dict with keys like "h_0_1" for horizontal edge between rows 0 and 1
        """
        patterns = {}
        
        # Generate horizontal edges (between rows)
        for row in range(self.rows - 1):
            for col in range(self.cols):
                key = f"h_{row}_{col}"
                # True = tab pointing down, False = blank (tab pointing up)
                patterns[key] = random.choice([True, False])
        
        # Generate vertical edges (between columns)
        for row in range(self.rows):
            for col in range(self.cols - 1):
                key = f"v_{row}_{col}"
                # True = tab pointing right, False = blank (tab pointing left)
                patterns[key] = random.choice([True, False])
        
        return patterns
    
    def _create_piece_mask(self, row: int, col: int, edge_patterns: dict, 
                          style: CuttingStyle) -> Image.Image:
        """
        Create a mask for a single puzzle piece.
        
        Args:
            row: Row index of the piece
            col: Column index of the piece
            edge_patterns: Dictionary of edge patterns
            style: Cutting style
            
        Returns:
            PIL Image mask (L mode) where white = piece, black = transparent
        """
        # Create a larger canvas to account for tabs extending beyond piece boundaries
        canvas_size = self.piece_size + 2 * self.tab_size
        mask = Image.new('L', (canvas_size, canvas_size), 0)
        draw = ImageDraw.Draw(mask)
        
        # Offset to center the piece in the canvas
        offset = self.tab_size
        
        if style == CuttingStyle.CLASSIC:
            # Draw classic jigsaw piece with tabs and blanks
            self._draw_classic_piece(draw, row, col, edge_patterns, offset)
        elif style == CuttingStyle.GEOMETRIC:
            # Draw geometric piece (straight edges with occasional angles)
            self._draw_geometric_piece(draw, row, col, offset)
        else:  # ORGANIC
            # Draw organic piece with natural curves
            self._draw_organic_piece(draw, row, col, offset)
        
        return mask
    
    def _draw_classic_piece(self, draw: ImageDraw.Draw, row: int, col: int, 
                           edge_patterns: dict, offset: int):
        """Draw a classic jigsaw piece with tabs and blanks"""
        # Start with base rectangle
        x0, y0 = offset, offset
        x1, y1 = offset + self.piece_size, offset + self.piece_size
        
        # Create polygon points for the piece
        points = []
        
        # Top edge
        points.extend(self._get_edge_points(x0, y0, x1, y0, 'horizontal',
                                          self._get_top_edge_type(row, col, edge_patterns)))
        
        # Right edge
        points.extend(self._get_edge_points(x1, y0, x1, y1, 'vertical',
                                          self._get_right_edge_type(row, col, edge_patterns)))
        
        # Bottom edge (reversed)
        bottom_points = self._get_edge_points(x1, y1, x0, y1, 'horizontal',
                                             self._get_bottom_edge_type(row, col, edge_patterns))
        points.extend(reversed(bottom_points))
        
        # Left edge (reversed)
        left_points = self._get_edge_points(x0, y1, x0, y0, 'vertical',
                                          self._get_left_edge_type(row, col, edge_patterns))
        points.extend(reversed(left_points))
        
        # Draw filled polygon
        draw.polygon(points, fill=255)
    
    def _get_edge_points(self, x0: float, y0: float, x1: float, y1: float,
                        direction: str, edge_type: str) -> List[Tuple[float, float]]:
        """
        Get points for drawing an edge with tabs/blanks.
        
        Args:
            x0, y0: Start point
            x1, y1: End point
            direction: 'horizontal' or 'vertical'
            edge_type: 'straight', 'tab', or 'blank'
            
        Returns:
            List of points for the edge
        """
        if edge_type == 'straight':
            return [(x0, y0), (x1, y1)]
        
        points = []
        
        # Add variation to tab position
        variation = (random.random() - 0.5) * self.tab_variation * self.piece_size
        
        if direction == 'horizontal':
            mid_x = (x0 + x1) / 2 + variation
            tab_height = self.tab_size if edge_type == 'tab' else -self.tab_size
            
            # Create more realistic jigsaw curve
            # Start segment length
            start_segment = (mid_x - x0) * 0.35
            
            points = [
                (x0, y0),
                # Lead-in to tab
                (x0 + start_segment, y0),
                (x0 + start_segment + 10, y0 + tab_height * 0.1),
                (x0 + start_segment + 15, y0 + tab_height * 0.3),
                (x0 + start_segment + 20, y0 + tab_height * 0.6),
                # Tab neck
                (mid_x - self.tab_size * 0.7, y0 + tab_height * 0.9),
                # Tab head (circular bulge)
                (mid_x - self.tab_size * 0.5, y0 + tab_height),
                (mid_x - self.tab_size * 0.3, y0 + tab_height * 1.1),
                (mid_x, y0 + tab_height * 1.15),
                (mid_x + self.tab_size * 0.3, y0 + tab_height * 1.1),
                (mid_x + self.tab_size * 0.5, y0 + tab_height),
                # Tab neck (other side)
                (mid_x + self.tab_size * 0.7, y0 + tab_height * 0.9),
                # Lead-out from tab
                (x1 - start_segment - 20, y0 + tab_height * 0.6),
                (x1 - start_segment - 15, y0 + tab_height * 0.3),
                (x1 - start_segment - 10, y0 + tab_height * 0.1),
                (x1 - start_segment, y0),
                (x1, y1)
            ]
        else:  # vertical
            mid_y = (y0 + y1) / 2 + variation
            tab_width = self.tab_size if edge_type == 'tab' else -self.tab_size
            
            # Create more realistic jigsaw curve
            start_segment = (mid_y - y0) * 0.35
            
            points = [
                (x0, y0),
                # Lead-in to tab
                (x0, y0 + start_segment),
                (x0 + tab_width * 0.1, y0 + start_segment + 10),
                (x0 + tab_width * 0.3, y0 + start_segment + 15),
                (x0 + tab_width * 0.6, y0 + start_segment + 20),
                # Tab neck
                (x0 + tab_width * 0.9, mid_y - self.tab_size * 0.7),
                # Tab head (circular bulge)
                (x0 + tab_width, mid_y - self.tab_size * 0.5),
                (x0 + tab_width * 1.1, mid_y - self.tab_size * 0.3),
                (x0 + tab_width * 1.15, mid_y),
                (x0 + tab_width * 1.1, mid_y + self.tab_size * 0.3),
                (x0 + tab_width, mid_y + self.tab_size * 0.5),
                # Tab neck (other side)
                (x0 + tab_width * 0.9, mid_y + self.tab_size * 0.7),
                # Lead-out from tab
                (x0 + tab_width * 0.6, y1 - start_segment - 20),
                (x0 + tab_width * 0.3, y1 - start_segment - 15),
                (x0 + tab_width * 0.1, y1 - start_segment - 10),
                (x0, y1 - start_segment),
                (x1, y1)
            ]
        
        return points
    
    def _get_top_edge_type(self, row: int, col: int, patterns: dict) -> str:
        """Get edge type for top edge of a piece"""
        if row == 0:
            return 'straight'
        key = f"h_{row-1}_{col}"
        return 'blank' if patterns.get(key, False) else 'tab'
    
    def _get_bottom_edge_type(self, row: int, col: int, patterns: dict) -> str:
        """Get edge type for bottom edge of a piece"""
        if row == self.rows - 1:
            return 'straight'
        key = f"h_{row}_{col}"
        return 'tab' if patterns.get(key, False) else 'blank'
    
    def _get_left_edge_type(self, row: int, col: int, patterns: dict) -> str:
        """Get edge type for left edge of a piece"""
        if col == 0:
            return 'straight'
        key = f"v_{row}_{col-1}"
        return 'blank' if patterns.get(key, False) else 'tab'
    
    def _get_right_edge_type(self, row: int, col: int, patterns: dict) -> str:
        """Get edge type for right edge of a piece"""
        if col == self.cols - 1:
            return 'straight'
        key = f"v_{row}_{col}"
        return 'tab' if patterns.get(key, False) else 'blank'
    
    def _draw_geometric_piece(self, draw: ImageDraw.Draw, row: int, col: int, offset: int):
        """Draw a geometric style piece with angular cuts"""
        # Simple implementation - can be enhanced
        x0, y0 = offset, offset
        x1, y1 = offset + self.piece_size, offset + self.piece_size
        
        # Add some angular variations
        points = []
        
        # Create angular edges with random variations
        variation = self.piece_size // 8
        
        # Top edge
        if row > 0:
            mid_x = (x0 + x1) // 2
            points.extend([(x0, y0), (mid_x - variation, y0 - variation), 
                          (mid_x + variation, y0 - variation), (x1, y0)])
        else:
            points.extend([(x0, y0), (x1, y0)])
        
        # Continue with other edges...
        points.extend([(x1, y1), (x0, y1), (x0, y0)])
        
        draw.polygon(points, fill=255)
    
    def _draw_organic_piece(self, draw: ImageDraw.Draw, row: int, col: int, offset: int):
        """Draw an organic style piece with natural curves"""
        # Simple implementation - uses wavy edges
        x0, y0 = offset, offset
        x1, y1 = offset + self.piece_size, offset + self.piece_size
        
        # Create organic curves using sine waves
        points = []
        steps = 20
        
        # Top edge with wave
        for i in range(steps + 1):
            t = i / steps
            x = x0 + (x1 - x0) * t
            wave = np.sin(t * np.pi * 2) * (self.piece_size // 10) if row > 0 else 0
            points.append((x, y0 + wave))
        
        # Continue with other edges...
        # Simplified for now
        points.extend([(x1, y1), (x0, y1)])
        
        draw.polygon(points, fill=255)
    
    def _extract_piece(self, image: Image.Image, row: int, col: int, 
                      mask: Image.Image) -> Image.Image:
        """
        Extract a puzzle piece from the full image using the mask.
        
        Args:
            image: Full puzzle image (RGBA)
            row: Row index of the piece
            col: Column index of the piece
            mask: Piece mask
            
        Returns:
            Extracted piece image with transparency
        """
        # Calculate the region to extract (with padding for tabs)
        x_start = col * self.piece_size - self.tab_size
        y_start = row * self.piece_size - self.tab_size
        x_end = x_start + mask.width
        y_end = y_start + mask.height
        
        # Ensure we don't go outside image bounds
        x_start = max(0, x_start)
        y_start = max(0, y_start)
        x_end = min(image.width, x_end)
        y_end = min(image.height, y_end)
        
        # Extract the region
        piece_region = image.crop((x_start, y_start, x_end, y_end))
        
        # Create a new image for the piece that's large enough for tabs
        # Use the mask size to ensure tabs aren't clipped
        piece = Image.new('RGBA', mask.size, (0, 0, 0, 0))
        
        # Apply mask to extracted region
        if piece_region.size != mask.size:
            # Adjust mask if needed due to boundary clipping
            mask_crop_x = 0 if x_start >= 0 else abs(x_start)
            mask_crop_y = 0 if y_start >= 0 else abs(y_start)
            mask = mask.crop((mask_crop_x, mask_crop_y, 
                            mask_crop_x + piece_region.width, 
                            mask_crop_y + piece_region.height))
        
        # Composite the piece
        piece_with_mask = Image.new('RGBA', piece_region.size)
        piece_with_mask.paste(piece_region, (0, 0))
        piece_with_mask.putalpha(mask)
        
        # Paste into final piece image at the correct offset
        paste_x = self.tab_size if x_start >= 0 else 0
        paste_y = self.tab_size if y_start >= 0 else 0
        piece.paste(piece_with_mask, (paste_x, paste_y), piece_with_mask)
        
        return piece