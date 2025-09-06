"""
Persona definitions for E2E testing
"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class PersonaDefinition:
    """Definition for a test persona."""
    name: str
    company_name: str
    company_type: str
    email: str
    role: str
    description: str


class PersonaRegistry:
    """Registry of all test personas."""
    
    PERSONAS = {
        "farmer": PersonaDefinition(
            name="Paula Martinez",
            company_name="Green Valley Farm",
            company_type="originator",
            email="paula@greenvalleyfarm.com",
            role="seller",
            description="Sustainable palm oil plantation in Malaysia"
        ),
        "processor": PersonaDefinition(
            name="Sam Chen",
            company_name="Pacific Processing Ltd",
            company_type="processor",
            email="sam@pacificprocessing.com",
            role="buyer",
            description="Palm oil processing and refining facility"
        ),
        "retailer": PersonaDefinition(
            name="Maria Rodriguez",
            company_name="EcoFood Brands",
            company_type="brand",
            email="maria@ecofoodbrands.com",
            role="buyer",
            description="Sustainable food brand focused on transparency"
        ),
        "consumer": PersonaDefinition(
            name="Charlie Thompson",
            company_name="Consumer Advocacy Group",
            company_type="brand",
            email="charlie@consumeradvocacy.org",
            role="viewer",
            description="Consumer transparency and advocacy organization"
        )
    }
    
    @classmethod
    def get_persona(cls, persona_type: str) -> PersonaDefinition:
        """Get persona definition by type."""
        if persona_type not in cls.PERSONAS:
            raise ValueError(f"Unknown persona type: {persona_type}")
        return cls.PERSONAS[persona_type]
    
    @classmethod
    def get_all_personas(cls) -> Dict[str, PersonaDefinition]:
        """Get all persona definitions."""
        return cls.PERSONAS.copy()