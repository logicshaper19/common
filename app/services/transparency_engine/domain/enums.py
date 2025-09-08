"""
Enums for transparency calculation engine.
"""
from enum import Enum


class TransparencyLevel(str, Enum):
    """Transparency level classifications."""
    VERY_LOW = "very_low"      # 0-20%
    LOW = "low"                # 20-40%
    MEDIUM = "medium"          # 40-60%
    HIGH = "high"              # 60-80%
    VERY_HIGH = "very_high"    # 80-100%


class ConfidenceLevel(str, Enum):
    """Confidence level in transparency calculations."""
    VERY_LOW = "very_low"      # 0-20%
    LOW = "low"                # 20-40%
    MEDIUM = "medium"          # 40-60%
    HIGH = "high"              # 60-80%
    VERY_HIGH = "very_high"    # 80-100%


class CertificationTier(str, Enum):
    """Certification value tiers for scoring."""
    BASIC = "basic"            # Basic certifications
    STANDARD = "standard"      # Standard industry certifications
    PREMIUM = "premium"        # High-value certifications (RSPO, etc.)
    ELITE = "elite"           # Elite certifications (multiple premium)


class DataCompletenessLevel(str, Enum):
    """Data completeness levels."""
    MINIMAL = "minimal"        # Basic required fields only
    PARTIAL = "partial"        # Some optional fields filled
    SUBSTANTIAL = "substantial" # Most fields filled
    COMPLETE = "complete"      # All fields filled


class ScoreType(str, Enum):
    """Types of transparency scores."""
    TTM = "ttm"               # Transparency to Market
    TTP = "ttp"               # Transparency to Producer
    COMBINED = "combined"      # Combined score


class GraphTraversalMode(str, Enum):
    """Graph traversal modes."""
    DEPTH_FIRST = "depth_first"
    BREADTH_FIRST = "breadth_first"
    WEIGHTED = "weighted"      # Weighted by quantity/importance


class CycleHandlingStrategy(str, Enum):
    """Strategies for handling circular references."""
    BREAK_AT_FIRST = "break_at_first"
    DEGRADATION = "degradation"
    WEIGHTED_AVERAGE = "weighted_average"
