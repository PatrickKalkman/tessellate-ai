import logging
from typing import Tuple

import cv2
import numpy as np
from scipy import stats

from ..core.config import settings
from ..core.models import QualityMetrics
from ..core.utils import image_to_array, load_image

logger = logging.getLogger(__name__)


class QualityGuardian:
    """Agent responsible for evaluating image quality for puzzle suitability"""

    def __init__(self, threshold: float = None):
        self.threshold = threshold or settings.quality_threshold

        # Weights for combining different metrics
        self.metric_weights = {
            "edge_density": 0.3,
            "color_entropy": 0.35,
            "local_contrast": 0.35,
        }

        # Thresholds for individual metrics (adjusted for lower quality threshold)
        self.min_thresholds = {
            "edge_density": 3.0,  # Minimum 3% edge pixels (was 10%)
            "color_entropy": 1.5,  # Minimum entropy of 1.5 (was 4.0)
            "local_contrast": 8.0,  # Minimum contrast std dev of 8 (was 20)
        }

    def evaluate(self, image_path: str) -> QualityMetrics:
        """
        Comprehensive quality assessment of an image for puzzle suitability.

        Args:
            image_path: Path to the image file

        Returns:
            QualityMetrics object with scores and overall assessment
        """
        logger.info(f"Evaluating image quality: {image_path}")

        # Load image
        image = load_image(image_path)
        image_array = image_to_array(image)

        # Calculate individual metrics
        edge_density = self.calculate_edge_density(image_array)
        color_entropy = self.calculate_color_entropy(image_array)
        local_contrast = self.calculate_local_contrast(image_array)

        # Check for disqualifying features
        if self._has_large_uniform_areas(image_array):
            logger.warning("Image has large uniform areas - reducing score")
            # Penalize images with large uniform areas
            edge_density *= 0.7
            local_contrast *= 0.7

        # Calculate weighted overall score
        overall_score = (
            self.metric_weights["edge_density"] * edge_density
            + self.metric_weights["color_entropy"]
            * color_entropy
            * 10  # Scale entropy to 0-100
            + self.metric_weights["local_contrast"] * local_contrast
        )

        # Ensure score is between 0 and 100
        overall_score = max(0, min(100, overall_score))

        metrics = QualityMetrics(
            edge_density=edge_density,
            color_entropy=color_entropy,
            local_contrast=local_contrast,
            overall_score=overall_score,
        )

        # Log detailed metrics
        logger.info(
            f"Quality metrics - Edge: {edge_density:.2f}%, "
            f"Entropy: {color_entropy:.2f}, "
            f"Contrast: {local_contrast:.2f}, "
            f"Overall: {overall_score:.2f}"
        )

        if not metrics.passes_threshold(self.threshold):
            reasons = self._get_failure_reasons(metrics)
            logger.warning(f"Image failed quality check: {', '.join(reasons)}")

        return metrics

    def calculate_edge_density(self, image: np.ndarray) -> float:
        """
        Calculate edge density using Canny edge detection.

        Args:
            image: Image as numpy array

        Returns:
            Percentage of pixels that are edges (0-100)
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image

        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Calculate good threshold values using Otsu's method
        high_thresh, _ = cv2.threshold(
            blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        low_thresh = 0.5 * high_thresh

        # Apply Canny edge detection
        edges = cv2.Canny(blurred, low_thresh, high_thresh)

        # Calculate edge density as percentage
        edge_pixels = np.sum(edges > 0)
        total_pixels = edges.shape[0] * edges.shape[1]
        edge_density = (edge_pixels / total_pixels) * 100

        return edge_density

    def calculate_color_entropy(self, image: np.ndarray) -> float:
        """
        Calculate Shannon entropy of color distribution using HSV color space.

        Args:
            image: Image as numpy array (RGB)

        Returns:
            Entropy value (typically 0-8, higher means more color variety)
        """
        # Convert to HSV for better color representation
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)

        # Create histograms for each channel
        hist_bins = 32  # Number of bins for histogram

        # Calculate histogram for each channel
        h_hist = cv2.calcHist([hsv], [0], None, [hist_bins], [0, 180])
        s_hist = cv2.calcHist([hsv], [1], None, [hist_bins], [0, 256])
        v_hist = cv2.calcHist([hsv], [2], None, [hist_bins], [0, 256])

        # Normalize histograms
        h_hist = h_hist.flatten() / h_hist.sum()
        s_hist = s_hist.flatten() / s_hist.sum()
        v_hist = v_hist.flatten() / v_hist.sum()

        # Calculate entropy for each channel
        h_entropy = stats.entropy(h_hist + 1e-10)  # Add small value to avoid log(0)
        s_entropy = stats.entropy(s_hist + 1e-10)
        v_entropy = stats.entropy(v_hist + 1e-10)

        # Combine entropies (weighted average, hue is most important for puzzles)
        total_entropy = 0.5 * h_entropy + 0.25 * s_entropy + 0.25 * v_entropy

        return total_entropy

    def calculate_local_contrast(self, image: np.ndarray) -> float:
        """
        Calculate local contrast using Sobel gradients.

        Args:
            image: Image as numpy array

        Returns:
            Standard deviation of gradient magnitudes (0-100)
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image

        # Apply Sobel filters
        sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)

        # Calculate gradient magnitude
        magnitude = np.sqrt(sobel_x**2 + sobel_y**2)

        # Calculate standard deviation of magnitudes
        contrast_std = np.std(magnitude)

        # Normalize to 0-100 range (typical values are 0-50)
        normalized_contrast = min(100, contrast_std * 2)

        return normalized_contrast

    def _has_large_uniform_areas(
        self, image: np.ndarray, threshold: float = 0.4
    ) -> bool:
        """
        Check if image has large uniform areas (like vast skies or walls).

        Args:
            image: Image as numpy array
            threshold: Fraction of image that can be uniform (default 40%)

        Returns:
            True if image has large uniform areas
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image

        # Calculate local standard deviation
        kernel_size = 15
        kernel = np.ones((kernel_size, kernel_size)) / (kernel_size * kernel_size)

        # Calculate local mean
        local_mean = cv2.filter2D(gray.astype(np.float32), -1, kernel)

        # Calculate local variance
        local_sq_mean = cv2.filter2D((gray.astype(np.float32)) ** 2, -1, kernel)
        local_variance = local_sq_mean - local_mean**2
        local_std = np.sqrt(np.maximum(local_variance, 0))

        # Count pixels with very low local standard deviation
        uniform_threshold = (
            5.0  # Pixels with std dev less than this are considered uniform
        )
        uniform_pixels = np.sum(local_std < uniform_threshold)
        total_pixels = gray.shape[0] * gray.shape[1]

        uniform_ratio = uniform_pixels / total_pixels

        return uniform_ratio > threshold

    def _get_failure_reasons(self, metrics: QualityMetrics) -> list[str]:
        """Get list of reasons why an image failed quality check"""
        reasons = []

        if metrics.edge_density < self.min_thresholds["edge_density"]:
            reasons.append(f"Low edge density ({metrics.edge_density:.1f}%)")

        if metrics.color_entropy < self.min_thresholds["color_entropy"]:
            reasons.append(f"Low color variety (entropy: {metrics.color_entropy:.1f})")

        if metrics.local_contrast < self.min_thresholds["local_contrast"]:
            reasons.append(f"Low contrast ({metrics.local_contrast:.1f})")

        if metrics.overall_score < self.threshold:
            reasons.append(f"Overall score too low ({metrics.overall_score:.1f})")

        return reasons

    def batch_evaluate(
        self, image_paths: list[str]
    ) -> list[Tuple[str, QualityMetrics]]:
        """
        Evaluate multiple images and return results.

        Args:
            image_paths: List of image file paths

        Returns:
            List of tuples (image_path, metrics)
        """
        results = []

        for path in image_paths:
            try:
                metrics = self.evaluate(path)
                results.append((path, metrics))
            except Exception as e:
                logger.error(f"Failed to evaluate {path}: {e}")
                # Create failed metrics
                failed_metrics = QualityMetrics(
                    edge_density=0, color_entropy=0, local_contrast=0, overall_score=0
                )
                results.append((path, failed_metrics))

        return results
