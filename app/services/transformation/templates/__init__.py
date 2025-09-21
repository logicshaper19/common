"""
Modular transformation template system.

This package provides a modular, testable, and maintainable architecture for
transformation template generation, following SOLID principles.
"""
from typing import Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from .base import TemplateEngineInterface, BaseTemplateEngine
from .plantation_template import PlantationTemplateEngine
from .mill_template import MillTemplateEngine
from .refinery_template import RefineryTemplateEngine
from .manufacturer_template import ManufacturerTemplateEngine
from .orchestrator import TransformationTemplateOrchestrator
from ..exceptions import TemplateGenerationError, ConfigurationError
from ..schemas import TransformationTemplateRequest


def create_template_engine(db: Session) -> TemplateEngineInterface:
    """Create a template engine with dependency injection."""
    return TransformationTemplateOrchestrator(db)


def create_plantation_template_engine() -> PlantationTemplateEngine:
    """Create a plantation-specific template engine."""
    return PlantationTemplateEngine()


def create_mill_template_engine() -> MillTemplateEngine:
    """Create a mill-specific template engine."""
    return MillTemplateEngine()


def create_refinery_template_engine() -> RefineryTemplateEngine:
    """Create a refinery-specific template engine."""
    return RefineryTemplateEngine()


def create_manufacturer_template_engine() -> ManufacturerTemplateEngine:
    """Create a manufacturer-specific template engine."""
    return ManufacturerTemplateEngine()
