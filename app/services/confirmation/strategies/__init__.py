"""
Confirmation strategies package.

Implements the strategy pattern for different confirmation interfaces.
"""

from .base import ConfirmationStrategy
from .context import ConfirmationStrategyContext
from .origin_data import OriginDataStrategy
from .transformation import TransformationStrategy
from .simple import SimpleConfirmationStrategy

__all__ = [
    "ConfirmationStrategy",
    "ConfirmationStrategyContext",
    "OriginDataStrategy", 
    "TransformationStrategy",
    "SimpleConfirmationStrategy"
]
