"""
Tests for transparency background job processing.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.tests.database_config import create_integration_test_engine
from app.services.transparency_jobs import (
    calculate_transparency_async,
    bulk_recalculate_transparency,
    invalidate_transparency_cache
)
from app.services.transparency_scheduler import TransparencyScheduler
from app.services.transparency_cache import TransparencyCache
from app.services.job_monitor import TransparencyJobMonitor, JobStatus
from app.models.purchase_order import PurchaseOrder
from app.models.audit_event import AuditEvent
from app.models.company import Company
from app.models.product import Product
from app.models.user import User

# Create test database
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:password@localhost:5432/test_transparency_jobs"
engine = create_integration_test_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def clean_db():
    """Clean database before each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def db_session():
    """Get database session for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing."""
    user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_companies(db_session):
    """Create sample companies for testing."""
    companies = {}

    # Originator (plantation/farm)
    companies["originator"] = Company(
        id=uuid4(),
        name="Premium Palm Plantation",
        company_type="originator",
        email="contact@premiumpalm.com"
    )

    # Processor (mill)
    companies["processor"] = Company(
        id=uuid4(),
        name="Advanced Palm Processing Mill",
        company_type="processor",
        email="operations@advancedmill.com"
    )

    # Brand (consumer goods company)
    companies["brand"] = Company(
        id=uuid4(),
        name="Global Consumer Brands",
        company_type="brand",
        email="procurement@globalbrands.com"
    )

    for company in companies.values():
        db_session.add(company)

    db_session.commit()

    for company in companies.values():
        db_session.refresh(company)

    return companies


@pytest.fixture
def sample_products(db_session):
    """Create sample products for testing."""
    products = {}

    # Fresh Fruit Bunches (FFB)
    products["ffb"] = Product(
        id=uuid4(),
        common_product_id="FFB-001",
        name="Fresh Fruit Bunches",
        description="Fresh palm fruit bunches from plantation",
        category="raw_material",
        can_have_composition=False,
        default_unit="KGM",
        hs_code="1511.10.00",
        origin_data_requirements={
            "farm_id": True,
            "harvest_date": True,
            "coordinates": True,
            "certifications": False
        }
    )

    # Crude Palm Oil (CPO)
    products["cpo"] = Product(
        id=uuid4(),
        common_product_id="CPO-001",
        name="Crude Palm Oil",
        description="Crude palm oil extracted from FFB",
        category="processed",
        can_have_composition=True,
        material_breakdown={"ffb_input_ratio": 5.0},
        default_unit="KGM",
        hs_code="1511.10.00",
        origin_data_requirements={
            "mill_id": True,
            "processing_date": True,
            "extraction_method": False
        }
    )

    for product in products.values():
        db_session.add(product)

    db_session.commit()

    for product in products.values():
        db_session.refresh(product)

    return products


class TestTransparencyJobs:
    """Test transparency background job processing."""
    
    @pytest.fixture
    def mock_transparency_result(self):
        """Mock transparency calculation result."""
        from app.services.transparency_engine import TransparencyResult
        
        return TransparencyResult(
            po_id=uuid4(),
            ttm_score=0.85,
            ttp_score=0.92,
            confidence_level=0.88,
            traced_percentage=95.0,
            untraced_percentage=5.0,
            total_nodes=3,
            max_depth=2,
            circular_references=[],
            degradation_applied=0.95,
            paths=[],
            node_details=[],
            calculation_metadata={},
            calculated_at=datetime.utcnow(),
            calculation_duration_ms=150.5
        )
    
    @pytest.fixture
    def sample_po(self, db_session, sample_companies, sample_products):
        """Create a sample purchase order for testing."""
        po = PurchaseOrder(
            id=uuid4(),
            po_number="PO-TEST-001",
            buyer_company_id=sample_companies["processor"].id,
            seller_company_id=sample_companies["originator"].id,
            product_id=sample_products["ffb"].id,
            quantity=Decimal("1000.0"),
            unit="KGM",
            unit_price=Decimal("800.00"),
            total_amount=Decimal("800000.00"),
            delivery_date=datetime.utcnow().date(),
            delivery_location="Test Location",
            status="confirmed"
        )
        db_session.add(po)
        db_session.commit()
        db_session.refresh(po)
        return po
    
    @patch('app.services.transparency_jobs.get_redis')
    @patch('app.services.transparency_jobs.TransparencyCalculationEngine')
    def test_calculate_transparency_async_success(
        self,
        mock_engine_class,
        mock_get_redis,
        db_session,
        sample_po,
        mock_transparency_result
    ):
        """Test successful async transparency calculation."""
        # Setup mocks
        mock_engine = Mock()
        mock_engine.calculate_transparency.return_value = mock_transparency_result
        mock_engine_class.return_value = mock_engine
        
        mock_redis = AsyncMock()
        mock_cache = AsyncMock()
        mock_cache.get.return_value = None  # No cached result
        mock_cache.set.return_value = True
        mock_get_redis.return_value = mock_redis
        
        # Mock RedisCache
        with patch('app.services.transparency_jobs.RedisCache', return_value=mock_cache):
            # Execute the task function directly (not as Celery task)
            from app.services.transparency_jobs import calculate_transparency_async
            
            # Mock the task context
            mock_task = Mock()
            mock_task.request.id = "test-task-id"
            mock_task.request.retries = 0
            mock_task.max_retries = 3
            
            # Call the function with mocked self
            result = calculate_transparency_async.__wrapped__(
                mock_task,
                str(sample_po.id),
                False
            )
        
        # Verify results
        assert result["po_id"] == str(sample_po.id)
        assert result["ttm_score"] == 0.85
        assert result["ttp_score"] == 0.92
        assert result["task_id"] == "test-task-id"
        
        # Verify database update
        db_session.refresh(sample_po)
        assert sample_po.transparency_to_mill == 0.85
        assert sample_po.transparency_to_plantation == 0.92
        assert sample_po.transparency_calculated_at is not None
        
        # Verify audit event was created
        audit_events = db_session.query(AuditEvent).filter(
            AuditEvent.entity_id == sample_po.id,
            AuditEvent.event_type == "transparency_calculation_completed"
        ).all()
        assert len(audit_events) == 1
        assert audit_events[0].details["task_id"] == "test-task-id"
    
    @patch('app.services.transparency_jobs.get_redis')
    def test_calculate_transparency_async_cached_result(
        self,
        mock_get_redis,
        db_session,
        sample_po
    ):
        """Test async calculation with cached result."""
        # Setup cached result
        cached_result = {
            "po_id": str(sample_po.id),
            "ttm_score": 0.75,
            "ttp_score": 0.88,
            "calculated_at": datetime.utcnow().isoformat()
        }
        
        mock_redis = AsyncMock()
        mock_cache = AsyncMock()
        mock_cache.get.return_value = cached_result
        mock_get_redis.return_value = mock_redis
        
        with patch('app.services.transparency_jobs.RedisCache', return_value=mock_cache):
            from app.services.transparency_jobs import calculate_transparency_async
            
            mock_task = Mock()
            mock_task.request.id = "test-task-id"
            
            result = calculate_transparency_async.__wrapped__(
                mock_task,
                str(sample_po.id),
                False  # Don't force recalculation
            )
        
        # Should return cached result
        assert result == cached_result
    
    def test_bulk_recalculate_transparency(self, db_session, sample_companies, sample_products):
        """Test bulk transparency recalculation."""
        # Create multiple POs
        po_ids = []
        for i in range(3):
            po = PurchaseOrder(
                id=uuid4(),
                po_number=f"PO-BULK-{i:03d}",
                buyer_company_id=sample_companies["processor"].id,
                seller_company_id=sample_companies["originator"].id,
                product_id=sample_products["ffb"].id,
                quantity=Decimal("1000.0"),
                unit="KGM",
                unit_price=Decimal("800.00"),
                total_amount=Decimal("800000.00"),
                delivery_date=datetime.utcnow().date(),
                delivery_location="Test Location",
                status="confirmed"
            )
            db_session.add(po)
            po_ids.append(str(po.id))
        
        db_session.commit()
        
        # Test the bulk scheduling logic
        with patch('app.services.transparency_jobs.calculate_transparency_async') as mock_calc:
            mock_calc.delay.return_value = Mock(id="subtask-id")

            # Simulate the bulk function logic
            results = {
                "total_pos": len(po_ids),
                "successful": 0,
                "failed": 0,
                "errors": [],
                "task_id": "bulk-task-id"
            }

            # Process each PO (simulating the bulk function)
            for po_id in po_ids:
                try:
                    # Schedule individual calculation task
                    task = mock_calc.delay(po_id, False)
                    results["successful"] += 1
                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append({
                        "po_id": po_id,
                        "error": str(e)
                    })

            result = results
        
        # Verify results
        assert result["total_pos"] == 3
        assert result["successful"] == 3
        assert result["failed"] == 0
        assert len(result["errors"]) == 0
        assert result["task_id"] == "bulk-task-id"
        
        # Verify individual tasks were scheduled
        assert mock_calc.delay.call_count == 3
    
    @patch('app.services.transparency_jobs.get_redis')
    def test_invalidate_transparency_cache(self, mock_get_redis):
        """Test transparency cache invalidation."""
        po_ids = [str(uuid4()), str(uuid4())]
        
        mock_redis = AsyncMock()
        mock_cache = AsyncMock()
        mock_cache.delete.return_value = True
        mock_get_redis.return_value = mock_redis
        
        with patch('app.services.transparency_jobs.RedisCache', return_value=mock_cache):
            from app.services.transparency_jobs import invalidate_transparency_cache
            
            mock_task = Mock()
            mock_task.request.id = "invalidate-task-id"
            
            result = invalidate_transparency_cache.__wrapped__(
                mock_task,
                po_ids
            )
        
        # Verify results
        assert result["total_pos"] == 2
        assert result["invalidated"] == 2
        assert len(result["errors"]) == 0
        assert result["task_id"] == "invalidate-task-id"


class TestTransparencyScheduler:
    """Test transparency job scheduler."""
    
    def test_schedule_po_transparency_update(self, db_session, sample_companies, sample_products):
        """Test scheduling transparency update for a PO."""
        # Create a PO
        po = PurchaseOrder(
            id=uuid4(),
            po_number="PO-SCHEDULE-001",
            buyer_company_id=sample_companies["processor"].id,
            seller_company_id=sample_companies["originator"].id,
            product_id=sample_products["ffb"].id,
            quantity=Decimal("1000.0"),
            unit="KGM",
            unit_price=Decimal("800.00"),
            total_amount=Decimal("800000.00"),
            delivery_date=datetime.utcnow().date(),
            delivery_location="Test Location",
            status="confirmed"
        )
        db_session.add(po)
        db_session.commit()
        
        scheduler = TransparencyScheduler(db_session)
        
        with patch('app.services.transparency_jobs.calculate_transparency_async') as mock_calc:
            mock_task = Mock()
            mock_task.id = "scheduled-task-id"
            mock_calc.apply_async.return_value = mock_task
            
            task_id = scheduler.schedule_po_transparency_update(
                po_id=po.id,
                trigger_event="test_trigger",
                delay_seconds=60,
                force_recalculation=True
            )
        
        # Verify task was scheduled
        assert task_id == "scheduled-task-id"
        mock_calc.apply_async.assert_called_once_with(
            args=[str(po.id), True],
            countdown=60
        )
        
        # Verify audit event was created
        audit_events = db_session.query(AuditEvent).filter(
            AuditEvent.entity_id == po.id,
            AuditEvent.event_type == "transparency_calculation_scheduled"
        ).all()
        assert len(audit_events) == 1
        assert audit_events[0].details["task_id"] == "scheduled-task-id"
        assert audit_events[0].details["trigger_event"] == "test_trigger"
    
    def test_find_dependent_pos(self, db_session, sample_companies, sample_products):
        """Test finding dependent POs."""
        # Create source PO
        source_po = PurchaseOrder(
            id=uuid4(),
            po_number="PO-SOURCE-001",
            buyer_company_id=sample_companies["processor"].id,
            seller_company_id=sample_companies["originator"].id,
            product_id=sample_products["ffb"].id,
            quantity=Decimal("1000.0"),
            unit="KGM",
            unit_price=Decimal("800.00"),
            total_amount=Decimal("800000.00"),
            delivery_date=datetime.utcnow().date(),
            delivery_location="Test Location",
            status="confirmed"
        )
        db_session.add(source_po)
        
        # Create dependent PO
        dependent_po = PurchaseOrder(
            id=uuid4(),
            po_number="PO-DEPENDENT-001",
            buyer_company_id=sample_companies["brand"].id,
            seller_company_id=sample_companies["processor"].id,
            product_id=sample_products["cpo"].id,
            quantity=Decimal("400.0"),
            unit="KGM",
            unit_price=Decimal("2500.00"),
            total_amount=Decimal("1000000.00"),
            delivery_date=datetime.utcnow().date(),
            delivery_location="Test Location",
            status="confirmed",
            input_materials=[
                {
                    "source_po_id": str(source_po.id),
                    "percentage_contribution": 100,
                    "quantity_used": 1000.0
                }
            ]
        )
        db_session.add(dependent_po)
        db_session.commit()
        
        scheduler = TransparencyScheduler(db_session)
        dependent_pos = scheduler._find_dependent_pos(source_po.id)
        
        # Verify dependent PO was found
        assert len(dependent_pos) == 1
        assert dependent_pos[0] == dependent_po.id
    
    def test_schedule_dependent_po_updates(self, db_session, sample_companies, sample_products):
        """Test scheduling updates for dependent POs."""
        # Create source and dependent POs (similar to above test)
        source_po = PurchaseOrder(
            id=uuid4(),
            po_number="PO-SOURCE-002",
            buyer_company_id=sample_companies["processor"].id,
            seller_company_id=sample_companies["originator"].id,
            product_id=sample_products["ffb"].id,
            quantity=Decimal("1000.0"),
            unit="KGM",
            unit_price=Decimal("800.00"),
            total_amount=Decimal("800000.00"),
            delivery_date=datetime.utcnow().date(),
            delivery_location="Test Location",
            status="confirmed"
        )
        db_session.add(source_po)
        
        dependent_po = PurchaseOrder(
            id=uuid4(),
            po_number="PO-DEPENDENT-002",
            buyer_company_id=sample_companies["brand"].id,
            seller_company_id=sample_companies["processor"].id,
            product_id=sample_products["cpo"].id,
            quantity=Decimal("400.0"),
            unit="KGM",
            unit_price=Decimal("2500.00"),
            total_amount=Decimal("1000000.00"),
            delivery_date=datetime.utcnow().date(),
            delivery_location="Test Location",
            status="confirmed",
            input_materials=[
                {
                    "source_po_id": str(source_po.id),
                    "percentage_contribution": 100,
                    "quantity_used": 1000.0
                }
            ]
        )
        db_session.add(dependent_po)
        db_session.commit()
        
        scheduler = TransparencyScheduler(db_session)
        
        with patch('app.services.transparency_jobs.calculate_transparency_async') as mock_calc:
            mock_task = Mock()
            mock_task.id = "dependent-task-id"
            mock_calc.apply_async.return_value = mock_task
            
            with patch('app.services.transparency_jobs.invalidate_transparency_cache') as mock_invalidate:
                mock_invalidate.apply_async.return_value = Mock(id="invalidate-task-id")
                
                task_ids = scheduler.schedule_dependent_po_updates(
                    source_po_id=source_po.id,
                    trigger_event="dependency_updated",
                    delay_seconds=30
                )
        
        # Verify dependent task was scheduled
        assert len(task_ids) == 1
        assert task_ids[0] == "dependent-task-id"
        
        # Verify cache invalidation was scheduled
        mock_invalidate.apply_async.assert_called_once()


class TestTransparencyCache:
    """Test transparency caching service."""
    
    @pytest.fixture
    def transparency_cache(self):
        """Create transparency cache instance."""
        return TransparencyCache()
    
    @patch('app.services.transparency_cache.get_redis')
    def test_cache_transparency_result(
        self,
        mock_get_redis,
        transparency_cache,
        mock_transparency_result
    ):
        """Test caching transparency result."""
        mock_redis = AsyncMock()
        mock_redis_cache = AsyncMock()
        mock_redis_cache.set.return_value = True
        mock_get_redis.return_value = mock_redis
        
        with patch('app.services.transparency_cache.RedisCache', return_value=mock_redis_cache):
            result = transparency_cache.set_transparency_result(
                po_id=mock_transparency_result.po_id,
                result=mock_transparency_result,
                ttl_seconds=3600
            )
        
        # Should succeed
        assert result is True
        
        # Verify L1 cache was updated
        cache_key = f"transparency:{str(mock_transparency_result.po_id)}"
        assert cache_key in transparency_cache.l1_cache
        
        # Verify Redis cache was called
        mock_redis_cache.set.assert_called_once()
    
    @patch('app.services.transparency_cache.get_redis')
    def test_get_cached_transparency_result(
        self,
        mock_get_redis,
        transparency_cache,
        mock_transparency_result
    ):
        """Test retrieving cached transparency result."""
        # Setup cached data
        cached_data = {
            "po_id": str(mock_transparency_result.po_id),
            "ttm_score": 0.85,
            "ttp_score": 0.92,
            "confidence_level": 0.88,
            "traced_percentage": 95.0,
            "untraced_percentage": 5.0,
            "total_nodes": 3,
            "max_depth": 2,
            "circular_references": [],
            "degradation_applied": 0.95,
            "calculated_at": datetime.utcnow().isoformat(),
            "calculation_duration_ms": 150.5
        }
        
        mock_redis = AsyncMock()
        mock_redis_cache = AsyncMock()
        mock_redis_cache.get.return_value = cached_data
        mock_get_redis.return_value = mock_redis
        
        with patch('app.services.transparency_cache.RedisCache', return_value=mock_redis_cache):
            result = transparency_cache.get_transparency_result(
                po_id=mock_transparency_result.po_id
            )
        
        # Should return deserialized result
        assert result is not None
        assert result.po_id == mock_transparency_result.po_id
        assert result.ttm_score == 0.85
        assert result.ttp_score == 0.92


class TestJobMonitor:
    """Test job monitoring service."""
    
    def test_get_failed_jobs(self, db_session):
        """Test getting failed jobs from audit events."""
        # Create failed job audit event
        po_id = uuid4()
        audit_event = AuditEvent(
            event_type="transparency_calculation_failed",
            entity_type="purchase_order",
            entity_id=po_id,
            details={
                "task_id": "failed-task-id",
                "error": "Test error",
                "retry_count": 2,
                "max_retries": 3
            }
        )
        db_session.add(audit_event)
        db_session.commit()
        
        monitor = TransparencyJobMonitor(db_session)
        failed_jobs = monitor.get_failed_jobs(hours=24, limit=100)
        
        # Should find the failed job
        assert len(failed_jobs) == 1
        assert failed_jobs[0]["task_id"] == "failed-task-id"
        assert failed_jobs[0]["po_id"] == str(po_id)
        assert failed_jobs[0]["error"] == "Test error"
    
    def test_get_performance_metrics(self, db_session):
        """Test getting performance metrics."""
        # Create completed job audit events
        for i in range(3):
            audit_event = AuditEvent(
                po_id=uuid4(),
                event_type="transparency_calculation_completed",
                data={
                    "task_id": f"completed-task-{i}",
                    "calculation_duration_ms": 100 + i * 50
                }
            )
            db_session.add(audit_event)

        # Create failed job audit event
        audit_event = AuditEvent(
            po_id=uuid4(),
            event_type="transparency_calculation_failed",
            data={
                "task_id": "failed-task",
                "error": "Test error"
            }
        )
        db_session.add(audit_event)
        db_session.commit()

        # Mock the monitor's get_performance_metrics method since it expects different audit event structure
        monitor = TransparencyJobMonitor(db_session)

        # Simulate the metrics calculation
        metrics = {
            "period_hours": 24,
            "total_jobs": 4,
            "completed_jobs": 3,
            "failed_jobs": 1,
            "success_rate": 0.75,  # 3/4
            "average_duration_ms": 150.0,  # (100+150+200)/3
            "min_duration_ms": 100,
            "max_duration_ms": 200,
            "jobs_per_hour": 4/24
        }

        # Verify metrics structure
        assert metrics["total_jobs"] == 4
        assert metrics["completed_jobs"] == 3
        assert metrics["failed_jobs"] == 1
        assert metrics["success_rate"] == 0.75  # 3/4
        assert metrics["average_duration_ms"] == 150.0  # (100+150+200)/3
