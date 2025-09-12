"""
Test data factories for realistic supply chain scenarios.
"""
import random
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta, date
from decimal import Decimal
from uuid import uuid4, UUID
from dataclasses import dataclass
from enum import Enum

from app.models.company import Company
from app.models.user import User
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder
from app.models.business_relationship import BusinessRelationship
from app.models.batch import Batch
from app.models.audit_event import AuditEvent


class SupplyChainTier(Enum):
    """Supply chain tier levels."""
    BRAND = "brand"
    PROCESSOR = "processor"
    ORIGINATOR = "originator"


@dataclass
class SupplyChainScenario:
    """Represents a complete supply chain scenario."""
    name: str
    description: str
    companies: List[Company]
    users: List[User]
    products: List[Product]
    relationships: List[BusinessRelationship]
    purchase_orders: List[PurchaseOrder]
    batches: List[Batch]
    complexity_level: str  # "simple", "medium", "complex"


class CompanyFactory:
    """Factory for creating realistic companies."""
    
    COMPANY_NAMES = {
        "brand": [
            "Global Fashion Co", "Sustainable Brands Inc", "Premium Textiles Ltd",
            "EcoWear International", "Fashion Forward Corp", "Green Apparel Group"
        ],
        "processor": [
            "Advanced Processing Ltd", "Textile Solutions Inc", "Manufacturing Excellence",
            "Process Innovation Co", "Industrial Textiles Ltd", "Quality Processing Corp"
        ],
        "originator": [
            "Organic Farms Ltd", "Sustainable Agriculture Co", "Natural Fibers Inc",
            "EcoFarm International", "Green Origins Ltd", "Pure Source Farms"
        ]
    }
    
    COUNTRIES = [
        "United States", "Germany", "India", "China", "Bangladesh", "Vietnam",
        "Turkey", "Brazil", "Indonesia", "Thailand", "Malaysia", "Pakistan"
    ]
    
    @classmethod
    def create_company(
        cls,
        company_type: str,
        name: Optional[str] = None,
        country: Optional[str] = None
    ) -> Company:
        """Create a realistic company."""
        if not name:
            name = random.choice(cls.COMPANY_NAMES[company_type])
        
        if not country:
            country = random.choice(cls.COUNTRIES)
        
        return Company(
            id=uuid4(),
            name=name,
            company_type=company_type,
            email=f"contact@{name.lower().replace(' ', '').replace(',', '').replace('.', '')}.com",
            phone=f"+{random.randint(1, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
            address_street=f"{random.randint(1, 999)} Business St",
            address_city=country,  # Using country as city for simplicity
            address_country=country,
            website=f"https://www.{name.lower().replace(' ', '').replace(',', '').replace('.', '')}.com",
            description=f"Leading {company_type} company specializing in sustainable supply chain operations."
        )
    
    @classmethod
    def create_supply_chain_tier(
        cls,
        tier: SupplyChainTier,
        count: int = 3
    ) -> List[Company]:
        """Create a tier of companies in the supply chain."""
        companies = []
        for i in range(count):
            company = cls.create_company(tier.value)
            companies.append(company)
        return companies


class UserFactory:
    """Factory for creating realistic users."""
    
    FIRST_NAMES = [
        "John", "Jane", "Michael", "Sarah", "David", "Emily", "Robert", "Lisa",
        "James", "Maria", "William", "Jennifer", "Richard", "Patricia", "Charles"
    ]
    
    LAST_NAMES = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
        "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez"
    ]
    
    ROLES_BY_COMPANY_TYPE = {
        "brand": ["admin", "buyer", "sustainability_manager"],
        "processor": ["admin", "seller", "production_manager", "quality_manager"],
        "originator": ["admin", "seller", "farm_manager", "compliance_officer"]
    }
    
    @classmethod
    def create_user(
        cls,
        company: Company,
        role: Optional[str] = None,
        is_admin: bool = False
    ) -> User:
        """Create a realistic user for a company."""
        first_name = random.choice(cls.FIRST_NAMES)
        last_name = random.choice(cls.LAST_NAMES)
        
        if not role:
            available_roles = cls.ROLES_BY_COMPANY_TYPE[company.company_type]
            role = "admin" if is_admin else random.choice(available_roles)
        
        email = f"{first_name.lower()}.{last_name.lower()}@{company.email.split('@')[1]}"
        
        return User(
            id=uuid4(),
            email=email,
            hashed_password="$2b$12$hashed_password_placeholder",
            full_name=f"{first_name} {last_name}",
            role=role,
            is_active=True,
            company_id=company.id,
            phone=f"+{random.randint(1, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
            department=role.replace("_", " ").title()
        )
    
    @classmethod
    def create_users_for_company(
        cls,
        company: Company,
        count: int = 3
    ) -> List[User]:
        """Create multiple users for a company."""
        users = []
        # Always create one admin
        admin_user = cls.create_user(company, is_admin=True)
        users.append(admin_user)
        
        # Create additional users
        for i in range(count - 1):
            user = cls.create_user(company)
            users.append(user)
        
        return users


class ProductFactory:
    """Factory for creating realistic products."""
    
    PRODUCT_CATEGORIES = {
        "raw_material": [
            "Organic Cotton", "Conventional Cotton", "Recycled Cotton",
            "Wool", "Silk", "Linen", "Hemp", "Bamboo Fiber"
        ],
        "processed": [
            "Cotton Yarn", "Dyed Fabric", "Printed Fabric", "Woven Fabric",
            "Knitted Fabric", "Finished Textile", "Cut Pieces"
        ],
        "finished_good": [
            "T-Shirt", "Jeans", "Dress", "Jacket", "Sweater", "Shirt",
            "Pants", "Skirt", "Blouse", "Coat"
        ]
    }
    
    HS_CODES = {
        "raw_material": ["5201", "5202", "5203", "5301", "5302"],
        "processed": ["5205", "5206", "5207", "5208", "5209"],
        "finished_good": ["6109", "6110", "6203", "6204", "6205"]
    }
    
    @classmethod
    def create_product(
        cls,
        category: str,
        name: Optional[str] = None,
        can_have_composition: Optional[bool] = None
    ) -> Product:
        """Create a realistic product."""
        if not name:
            name = random.choice(cls.PRODUCT_CATEGORIES[category])
        
        if can_have_composition is None:
            can_have_composition = category in ["processed", "finished_good"]
        
        hs_code = random.choice(cls.HS_CODES[category])
        
        return Product(
            id=uuid4(),
            common_product_id=f"PROD-{category.upper()[:3]}-{random.randint(1000, 9999)}",
            name=name,
            category=category,
            description=f"High-quality {name.lower()} for sustainable supply chains",
            hs_code=hs_code,
            default_unit="KGM" if category == "raw_material" else "PCS",
            can_have_composition=can_have_composition,
            sustainability_certifications=cls._generate_certifications(category),
            origin_data_requirements=cls._generate_origin_requirements(category)
        )
    
    @classmethod
    def _generate_certifications(cls, category: str) -> List[str]:
        """Generate realistic sustainability certifications."""
        all_certs = [
            "GOTS", "OCS", "RCS", "OEKO-TEX", "Cradle to Cradle",
            "Fair Trade", "Organic", "BCI", "ZDHC"
        ]
        
        if category == "raw_material":
            return random.sample(all_certs[:6], k=random.randint(1, 3))
        elif category == "processed":
            return random.sample(all_certs[3:], k=random.randint(1, 2))
        else:
            return random.sample(all_certs, k=random.randint(0, 2))
    
    @classmethod
    def _generate_origin_requirements(cls, category: str) -> Dict[str, Any]:
        """Generate origin data requirements."""
        if category == "raw_material":
            return {
                "coordinates": {"required": True, "type": "farm_location"},
                "harvest_date": {"required": True, "type": "date"},
                "certifications": {"required": True, "type": "list"},
                "farmer_info": {"required": False, "type": "object"}
            }
        elif category == "processed":
            return {
                "facility_location": {"required": True, "type": "coordinates"},
                "processing_date": {"required": True, "type": "date"},
                "input_materials": {"required": True, "type": "list"}
            }
        else:
            return {
                "manufacturing_location": {"required": True, "type": "coordinates"},
                "production_date": {"required": True, "type": "date"}
            }
    
    @classmethod
    def create_product_catalog(cls) -> List[Product]:
        """Create a comprehensive product catalog."""
        products = []
        
        # Raw materials
        for _ in range(8):
            product = cls.create_product("raw_material")
            products.append(product)
        
        # Processed materials
        for _ in range(6):
            product = cls.create_product("processed")
            products.append(product)
        
        # Finished goods
        for _ in range(10):
            product = cls.create_product("finished_good")
            products.append(product)
        
        return products


class PurchaseOrderFactory:
    """Factory for creating realistic purchase orders."""
    
    PO_STATUSES = ["draft", "pending", "confirmed", "delivered", "cancelled"]
    
    @classmethod
    def create_purchase_order(
        cls,
        buyer_company: Company,
        seller_company: Company,
        product: Product,
        status: str = "pending",
        quantity: Optional[Decimal] = None,
        input_materials: Optional[List[Dict[str, Any]]] = None,
        origin_data: Optional[Dict[str, Any]] = None
    ) -> PurchaseOrder:
        """Create a realistic purchase order."""
        if not quantity:
            if product.default_unit == "KGM":
                quantity = Decimal(str(random.randint(100, 10000)))
            else:
                quantity = Decimal(str(random.randint(50, 5000)))
        
        delivery_date = date.today() + timedelta(days=random.randint(7, 90))
        
        po = PurchaseOrder(
            id=uuid4(),
            po_number=f"PO-{buyer_company.name[:3].upper()}-{random.randint(10000, 99999)}",
            buyer_company_id=buyer_company.id,
            seller_company_id=seller_company.id,
            product_id=product.id,
            quantity=quantity,
            unit=product.default_unit,
            status=status,
            delivery_date=delivery_date,
            notes=f"Purchase order for {product.name} - {quantity} {product.default_unit}",
            input_materials=input_materials,
            origin_data=origin_data
        )
        
        if status in ["confirmed", "delivered"]:
            po.confirmed_at = datetime.utcnow() - timedelta(days=random.randint(1, 30))
            po.confirmed_quantity = quantity
        
        return po
    
    @classmethod
    def create_supply_chain(
        cls,
        companies_by_tier: Dict[str, List[Company]],
        products_by_category: Dict[str, List[Product]],
        chain_length: int = 3
    ) -> List[PurchaseOrder]:
        """Create a realistic supply chain of connected purchase orders."""
        purchase_orders = []
        
        # Create the supply chain from originator to brand
        tiers = ["originator", "processor", "brand"]
        
        for i in range(len(tiers) - 1):
            current_tier = tiers[i]
            next_tier = tiers[i + 1]
            
            # Determine product categories for this tier
            if current_tier == "originator":
                product_category = "raw_material"
            elif current_tier == "processor":
                product_category = "processed"
            else:
                product_category = "finished_good"
            
            # Create POs between companies in adjacent tiers
            for seller in companies_by_tier[current_tier]:
                for buyer in companies_by_tier[next_tier]:
                    # Create 1-3 POs between each pair
                    num_pos = random.randint(1, 3)
                    
                    for _ in range(num_pos):
                        product = random.choice(products_by_category[product_category])
                        
                        # Create input materials for processed/finished goods
                        input_materials = None
                        if product_category in ["processed", "finished_good"] and purchase_orders:
                            input_materials = cls._create_input_materials(purchase_orders)
                        
                        # Create origin data for raw materials
                        origin_data = None
                        if product_category == "raw_material":
                            origin_data = cls._create_origin_data()
                        
                        po = cls.create_purchase_order(
                            buyer_company=buyer,
                            seller_company=seller,
                            product=product,
                            status=random.choice(["confirmed", "delivered"]),
                            input_materials=input_materials,
                            origin_data=origin_data
                        )
                        purchase_orders.append(po)
        
        return purchase_orders
    
    @classmethod
    def _create_input_materials(
        cls,
        available_pos: List[PurchaseOrder]
    ) -> List[Dict[str, Any]]:
        """Create realistic input materials linking to previous POs."""
        if not available_pos:
            return []
        
        # Select 1-3 input POs
        num_inputs = min(random.randint(1, 3), len(available_pos))
        input_pos = random.sample(available_pos, num_inputs)
        
        input_materials = []
        total_percentage = 0
        
        for i, input_po in enumerate(input_pos):
            if i == len(input_pos) - 1:
                # Last input gets remaining percentage
                percentage = 100 - total_percentage
            else:
                # Random percentage, ensuring we don't exceed 100%
                max_percentage = min(80, 100 - total_percentage - (len(input_pos) - i - 1) * 10)
                percentage = random.randint(10, max_percentage)
            
            total_percentage += percentage
            
            input_materials.append({
                "source_po_id": str(input_po.id),
                "quantity_used": float(input_po.quantity * Decimal(str(percentage / 100))),
                "percentage_contribution": percentage,
                "material_type": "primary" if i == 0 else "secondary"
            })
        
        return input_materials
    
    @classmethod
    def _create_origin_data(cls) -> Dict[str, Any]:
        """Create realistic origin data."""
        # Generate random coordinates (focusing on major agricultural regions)
        regions = [
            {"lat": 28.6139, "lng": 77.2090, "region": "India"},
            {"lat": 31.2304, "lng": 121.4737, "region": "China"},
            {"lat": 23.8103, "lng": 90.4125, "region": "Bangladesh"},
            {"lat": 39.9042, "lng": 116.4074, "region": "China"},
            {"lat": -23.5505, "lng": -46.6333, "region": "Brazil"}
        ]
        
        region = random.choice(regions)
        
        return {
            "coordinates": {
                "lat": region["lat"] + random.uniform(-2, 2),
                "lng": region["lng"] + random.uniform(-2, 2)
            },
            "region": region["region"],
            "farm_name": f"Sustainable Farm {random.randint(1, 999)}",
            "harvest_date": (date.today() - timedelta(days=random.randint(30, 365))).isoformat(),
            "certifications": random.sample(["Organic", "Fair Trade", "GOTS", "BCI"], k=random.randint(1, 3)),
            "farmer_info": {
                "name": f"Farmer {random.choice(['Ahmed', 'Priya', 'Chen', 'Maria', 'John'])}",
                "farm_size_hectares": random.randint(5, 500),
                "years_experience": random.randint(5, 40)
            },
            "quality_metrics": {
                "fiber_length": random.uniform(25, 35),
                "moisture_content": random.uniform(6, 12),
                "purity_percentage": random.uniform(95, 99.5)
            }
        }


class BusinessRelationshipFactory:
    """Factory for creating business relationships."""
    
    RELATIONSHIP_TYPES = ["supplier", "customer", "partner", "subcontractor"]
    
    @classmethod
    def create_relationship(
        cls,
        buyer_company: Company,
        seller_company: Company,
        relationship_type: str = "supplier",
        status: str = "active"
    ) -> BusinessRelationship:
        """Create a business relationship."""
        return BusinessRelationship(
            id=uuid4(),
            buyer_company_id=buyer_company.id,
            seller_company_id=seller_company.id,
            relationship_type=relationship_type,
            status=status,
            invited_by_company_id=buyer_company.id,
            established_at=datetime.utcnow() - timedelta(days=random.randint(1, 365)),
            metadata={
                "invitation_method": "email",
                "onboarding_completed": True,
                "data_sharing_level": "standard",
                "preferred_communication": "email"
            }
        )
    
    @classmethod
    def create_supply_chain_relationships(
        cls,
        companies_by_tier: Dict[str, List[Company]]
    ) -> List[BusinessRelationship]:
        """Create relationships for a complete supply chain."""
        relationships = []
        tiers = ["originator", "processor", "brand"]
        
        for i in range(len(tiers) - 1):
            current_tier = tiers[i]
            next_tier = tiers[i + 1]
            
            for seller in companies_by_tier[current_tier]:
                for buyer in companies_by_tier[next_tier]:
                    relationship = cls.create_relationship(
                        buyer_company=buyer,
                        seller_company=seller,
                        relationship_type="supplier"
                    )
                    relationships.append(relationship)
        
        return relationships


class SupplyChainScenarioFactory:
    """Factory for creating complete supply chain scenarios."""
    
    @classmethod
    def create_simple_scenario(cls) -> SupplyChainScenario:
        """Create a simple 3-tier supply chain scenario."""
        # Create companies
        companies_by_tier = {
            "originator": CompanyFactory.create_supply_chain_tier(SupplyChainTier.ORIGINATOR, 1),
            "processor": CompanyFactory.create_supply_chain_tier(SupplyChainTier.PROCESSOR, 1),
            "brand": CompanyFactory.create_supply_chain_tier(SupplyChainTier.BRAND, 1)
        }
        
        all_companies = []
        for tier_companies in companies_by_tier.values():
            all_companies.extend(tier_companies)
        
        # Create users
        all_users = []
        for company in all_companies:
            users = UserFactory.create_users_for_company(company, count=2)
            all_users.extend(users)
        
        # Create products
        products = ProductFactory.create_product_catalog()
        products_by_category = {
            "raw_material": [p for p in products if p.category == "raw_material"][:3],
            "processed": [p for p in products if p.category == "processed"][:2],
            "finished_good": [p for p in products if p.category == "finished_good"][:3]
        }
        
        # Create relationships
        relationships = BusinessRelationshipFactory.create_supply_chain_relationships(companies_by_tier)
        
        # Create purchase orders
        purchase_orders = PurchaseOrderFactory.create_supply_chain(
            companies_by_tier, products_by_category, chain_length=3
        )
        
        return SupplyChainScenario(
            name="Simple Supply Chain",
            description="A basic 3-tier supply chain with one company per tier",
            companies=all_companies,
            users=all_users,
            products=sum(products_by_category.values(), []),
            relationships=relationships,
            purchase_orders=purchase_orders,
            batches=[],
            complexity_level="simple"
        )
    
    @classmethod
    def create_complex_scenario(cls) -> SupplyChainScenario:
        """Create a complex multi-tier supply chain scenario."""
        # Create companies (multiple per tier)
        companies_by_tier = {
            "originator": CompanyFactory.create_supply_chain_tier(SupplyChainTier.ORIGINATOR, 4),
            "processor": CompanyFactory.create_supply_chain_tier(SupplyChainTier.PROCESSOR, 3),
            "brand": CompanyFactory.create_supply_chain_tier(SupplyChainTier.BRAND, 2)
        }
        
        all_companies = []
        for tier_companies in companies_by_tier.values():
            all_companies.extend(tier_companies)
        
        # Create users (more per company)
        all_users = []
        for company in all_companies:
            user_count = 4 if company.company_type == "brand" else 3
            users = UserFactory.create_users_for_company(company, count=user_count)
            all_users.extend(users)
        
        # Create comprehensive product catalog
        products = ProductFactory.create_product_catalog()
        products_by_category = {
            "raw_material": [p for p in products if p.category == "raw_material"],
            "processed": [p for p in products if p.category == "processed"],
            "finished_good": [p for p in products if p.category == "finished_good"]
        }
        
        # Create relationships (more complex network)
        relationships = BusinessRelationshipFactory.create_supply_chain_relationships(companies_by_tier)
        
        # Add some cross-tier relationships for complexity
        for originator in companies_by_tier["originator"][:2]:
            for brand in companies_by_tier["brand"]:
                relationship = BusinessRelationshipFactory.create_relationship(
                    buyer_company=brand,
                    seller_company=originator,
                    relationship_type="direct_supplier"
                )
                relationships.append(relationship)
        
        # Create purchase orders (more complex chains)
        purchase_orders = PurchaseOrderFactory.create_supply_chain(
            companies_by_tier, products_by_category, chain_length=4
        )
        
        # Add some additional POs for complexity
        for _ in range(20):
            buyer = random.choice(all_companies)
            seller = random.choice(all_companies)
            if buyer != seller and buyer.company_type != "originator":
                product = random.choice(products)
                po = PurchaseOrderFactory.create_purchase_order(
                    buyer_company=buyer,
                    seller_company=seller,
                    product=product,
                    status=random.choice(["confirmed", "delivered", "pending"])
                )
                purchase_orders.append(po)
        
        return SupplyChainScenario(
            name="Complex Supply Chain Network",
            description="A complex multi-tier supply chain with multiple companies per tier and cross-connections",
            companies=all_companies,
            users=all_users,
            products=products,
            relationships=relationships,
            purchase_orders=purchase_orders,
            batches=[],
            complexity_level="complex"
        )
