#!/usr/bin/env python3
"""
Tessellate-AI CLI - Generate high-quality jigsaw puzzles using AI agents.
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

# Fix imports when running as a script
if __name__ == '__main__':
    backend_dir = Path(__file__).parent.absolute()
    parent_dir = backend_dir.parent
    sys.path.insert(0, str(parent_dir))

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.panel import Panel
from rich import box
from openai import OpenAI

# Try absolute imports first, fall back to relative
try:
    from backend.agents.prompt_artisan import PromptArtisan
    from backend.agents.quality_guardian import QualityGuardian
    from backend.agents.digital_cutter import DigitalCutter
    from backend.core.config import settings
    from backend.core.models import CuttingStyle, PuzzleGenerationStatus, PuzzleGenerationResult
    from backend.core.utils import setup_logging, ensure_directory, format_puzzle_id, console
except ImportError:
    from agents.prompt_artisan import PromptArtisan
    from agents.quality_guardian import QualityGuardian
    from agents.digital_cutter import DigitalCutter
    from core.config import settings
    from core.models import CuttingStyle, PuzzleGenerationStatus, PuzzleGenerationResult
    from core.utils import setup_logging, ensure_directory, format_puzzle_id, console


# Setup logging
logger = setup_logging(settings.log_level)


class PuzzleGenerator:
    """Main orchestrator for puzzle generation pipeline"""
    
    def __init__(self):
        self.console = console
        self.openai_client = OpenAI(api_key=settings.openai_api_key)
        
        # Initialize agents
        self.artisan = PromptArtisan(self.openai_client)
        self.guardian = QualityGuardian(settings.quality_threshold)
        self.cutter = DigitalCutter(settings.grid_size)
        
        # Statistics
        self.stats = {
            'attempts': 0,
            'accepted': 0,
            'rejected': 0,
            'failed': 0,
            'start_time': datetime.now()
        }
    
    def generate_puzzles(self, count: int, output_dir: str, 
                        complexity: float = 0.5, style: CuttingStyle = CuttingStyle.CLASSIC):
        """
        Generate multiple puzzles through the agent pipeline.
        
        Args:
            count: Number of puzzles to generate
            output_dir: Output directory for puzzles
            complexity: Complexity level (0-1)
            style: Cutting style for pieces
        """
        output_path = ensure_directory(output_dir)
        
        # Display header
        self._display_header(count, complexity, style)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=self.console
        ) as progress:
            
            main_task = progress.add_task(
                f"[cyan]Generating {count} puzzles...", 
                total=count
            )
            
            puzzles_created = 0
            
            while puzzles_created < count:
                self.stats['attempts'] += 1
                puzzle_id = format_puzzle_id(puzzles_created)
                
                # Update progress description
                progress.update(
                    main_task, 
                    description=f"[cyan]Creating puzzle {puzzles_created + 1}/{count} (Attempt {self.stats['attempts']})"
                )
                
                try:
                    # Generate puzzle
                    result = self._generate_single_puzzle(
                        puzzle_id, output_path, complexity, style, progress
                    )
                    
                    if result.status == PuzzleGenerationStatus.COMPLETED:
                        puzzles_created += 1
                        self.stats['accepted'] += 1
                        progress.update(main_task, advance=1)
                        
                        # Display success message
                        self.console.print(
                            f"✅ Puzzle {puzzle_id} created successfully! "
                            f"(Score: {result.quality_metrics.overall_score:.1f})"
                        )
                    else:
                        self.stats['rejected'] += 1
                        self.console.print(
                            f"❌ Puzzle attempt {self.stats['attempts']} rejected: "
                            f"{result.error_message}"
                        )
                
                except Exception as e:
                    self.stats['failed'] += 1
                    logger.error(f"Failed to generate puzzle: {e}")
                    self.console.print(f"[red]⚠️  Error: {str(e)}[/red]")
        
        # Display summary
        self._display_summary()
    
    def _generate_single_puzzle(self, puzzle_id: str, output_path: Path, 
                               complexity: float, style: CuttingStyle, 
                               progress: Progress) -> PuzzleGenerationResult:
        """Generate a single puzzle through the pipeline"""
        
        sub_task = progress.add_task("[yellow]Processing...", total=4)
        
        try:
            # Step 1: Generate prompt and image
            progress.update(sub_task, description="[yellow]🎨 Generating image prompt...")
            prompt = self.artisan.generate_prompt(complexity)
            
            progress.update(sub_task, description="[yellow]🖼️  Creating image with DALL-E 3...")
            image_result = self.artisan.create_image(prompt)
            progress.update(sub_task, advance=1)
            
            # Save temporary image
            temp_image = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            temp_image.write(image_result.image_data)
            temp_image.close()
            
            # Step 2: Quality check
            progress.update(sub_task, description="[yellow]🔍 Evaluating image quality...")
            metrics = self.guardian.evaluate(temp_image.name)
            progress.update(sub_task, advance=1)
            
            if not metrics.passes_threshold(settings.quality_threshold):
                # Clean up temp file
                os.unlink(temp_image.name)
                return PuzzleGenerationResult(
                    puzzle_id=puzzle_id,
                    status=PuzzleGenerationStatus.FAILED,
                    prompt=prompt,
                    quality_metrics=metrics,
                    error_message=f"Quality score too low: {metrics.overall_score:.1f}"
                )
            
            # Step 3: Cut into pieces
            progress.update(sub_task, description="[yellow]✂️  Cutting puzzle pieces...")
            puzzle_dir = output_path / puzzle_id
            manifest = self.cutter.cut_puzzle(temp_image.name, str(puzzle_dir), style)
            progress.update(sub_task, advance=1)
            
            # Step 4: Save original image
            progress.update(sub_task, description="[yellow]💾 Saving puzzle data...")
            original_path = puzzle_dir / "original.jpg"
            shutil.copy(temp_image.name, original_path)
            
            # Save generation metadata
            metadata = {
                "puzzle_id": puzzle_id,
                "prompt": prompt,
                "complexity": complexity,
                "style": style.value,
                "quality_metrics": metrics.model_dump(),
                "timestamp": datetime.now().isoformat(),
                "total_pieces": len(manifest.pieces)
            }
            
            import json
            with open(puzzle_dir / "metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)
            
            progress.update(sub_task, advance=1)
            
            # Clean up temp file
            os.unlink(temp_image.name)
            
            # Remove sub-task from progress
            progress.remove_task(sub_task)
            
            return PuzzleGenerationResult(
                puzzle_id=puzzle_id,
                status=PuzzleGenerationStatus.COMPLETED,
                prompt=prompt,
                quality_metrics=metrics
            )
            
        except Exception as e:
            # Clean up on error
            if 'temp_image' in locals() and os.path.exists(temp_image.name):
                os.unlink(temp_image.name)
            
            progress.remove_task(sub_task)
            
            return PuzzleGenerationResult(
                puzzle_id=puzzle_id,
                status=PuzzleGenerationStatus.FAILED,
                prompt=prompt if 'prompt' in locals() else "",
                error_message=str(e)
            )
    
    def _display_header(self, count: int, complexity: float, style: CuttingStyle):
        """Display welcome header"""
        header = Panel(
            f"[bold cyan]Tessellate-AI Puzzle Generator[/bold cyan]\n\n"
            f"Generating [bold]{count}[/bold] puzzles\n"
            f"Complexity: [bold]{complexity:.1%}[/bold]\n"
            f"Style: [bold]{style.value}[/bold]\n"
            f"Grid: [bold]{settings.grid_rows}x{settings.grid_cols}[/bold] "
            f"([bold]{settings.total_pieces}[/bold] pieces)",
            box=box.DOUBLE,
            expand=False
        )
        self.console.print(header)
        self.console.print()
    
    def _display_summary(self):
        """Display generation summary"""
        duration = (datetime.now() - self.stats['start_time']).total_seconds()
        
        # Create summary table
        table = Table(title="Generation Summary", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Attempts", str(self.stats['attempts']))
        table.add_row("Puzzles Created", str(self.stats['accepted']))
        table.add_row("Images Rejected", str(self.stats['rejected']))
        table.add_row("Errors", str(self.stats['failed']))
        table.add_row("Success Rate", f"{self.stats['accepted']/self.stats['attempts']*100:.1f}%")
        table.add_row("Time Elapsed", f"{duration:.1f}s")
        table.add_row("Avg Time/Puzzle", f"{duration/self.stats['accepted']:.1f}s" if self.stats['accepted'] > 0 else "N/A")
        
        self.console.print()
        self.console.print(table)


@click.command()
@click.option('--count', '-c', default=20, help='Number of puzzles to generate')
@click.option('--output', '-o', default='public/puzzles', help='Output directory')
@click.option('--complexity', '-x', default=0.5, type=float, help='Complexity level (0-1)')
@click.option('--style', '-s', 
              type=click.Choice(['rectangular', 'classic', 'geometric', 'organic']), 
              default='rectangular',
              help='Cutting style for pieces')
@click.option('--debug', is_flag=True, help='Enable debug logging')
def main(count, output, complexity, style, debug):
    """Generate high-quality jigsaw puzzles using AI agents."""
    
    # Update debug setting
    if debug:
        settings.debug = True
        settings.log_level = "DEBUG"
        logger.setLevel(logging.DEBUG)
    
    # Validate complexity
    if not 0 <= complexity <= 1:
        click.echo("Error: Complexity must be between 0 and 1", err=True)
        sys.exit(1)
    
    # Convert style string to enum
    style_enum = CuttingStyle(style)
    
    # Create generator and run
    generator = PuzzleGenerator()
    
    try:
        generator.generate_puzzles(count, output, complexity, style_enum)
    except KeyboardInterrupt:
        console.print("\n[yellow]Generation interrupted by user[/yellow]")
        generator._display_summary()
    except Exception as e:
        console.print(f"\n[red]Fatal error: {e}[/red]")
        if debug:
            console.print_exception()
        sys.exit(1)


if __name__ == '__main__':
    main()