"""
Notification and Alert Management Functions
Handles system notifications, alerts, and communication management.
"""
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
from enum import Enum

from .certification_cache import cached, performance_tracked
from .secure_query_builder import (
    SecureQueryBuilder, QueryOperator, execute_secure_query, SecureQueryError
)

logger = logging.getLogger(__name__)

class NotificationType(Enum):
    SYSTEM = "system"
    ALERT = "alert"
    REMINDER = "reminder"
    UPDATE = "update"
    WARNING = "warning"
    ERROR = "error"

class NotificationPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class NotificationStatus(Enum):
    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"
    DISMISSED = "dismissed"

class DeliveryChannel(Enum):
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"

@dataclass
class NotificationInfo:
    """Notification information and metadata."""
    id: str
    user_id: str
    user_name: str
    company_id: str
    company_name: str
    notification_type: str
    priority: str
    status: str
    title: str
    message: str
    data: Dict[str, Any]
    created_at: datetime
    read_at: Optional[datetime]
    expires_at: Optional[datetime]
    action_url: Optional[str]
    category: str
    delivery_channels: List[str]
    retry_count: int

@dataclass
class AlertRule:
    """Alert rule configuration."""
    id: str
    name: str
    description: str
    condition_type: str  # 'threshold', 'change', 'schedule', 'event'
    conditions: Dict[str, Any]
    alert_level: str
    target_audience: List[str]  # roles, companies, or specific users
    notification_template: str
    delivery_channels: List[str]
    is_active: bool
    created_by: str
    created_at: datetime
    last_triggered: Optional[datetime]
    trigger_count: int

@dataclass
class NotificationPreferences:
    """User notification preferences."""
    user_id: str
    email_notifications: bool
    sms_notifications: bool
    in_app_notifications: bool
    webhook_notifications: bool
    digest_frequency: str  # 'immediate', 'hourly', 'daily', 'weekly'
    categories_enabled: List[str]
    quiet_hours_start: Optional[str]
    quiet_hours_end: Optional[str]
    timezone: str

@dataclass
class NotificationDelivery:
    """Notification delivery tracking."""
    id: str
    notification_id: str
    delivery_channel: str
    delivery_status: str  # 'pending', 'sent', 'delivered', 'failed'
    delivery_address: str  # email, phone, webhook URL
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    error_message: Optional[str]
    retry_count: int
    next_retry_at: Optional[datetime]

class NotificationManager:
    """Notification and alert management functions."""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    @cached(ttl=60)  # 1-minute cache for real-time notifications
    @performance_tracked
    def get_notifications(
        self,
        user_id: Optional[str] = None,
        company_id: Optional[str] = None,
        notification_type: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        unread_only: bool = False,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 50
    ) -> Tuple[List[NotificationInfo], Dict[str, Any]]:
        """
        Get notifications with filtering and status tracking.
        
        Args:
            user_id: Filter by specific user
            company_id: Filter by company
            notification_type: Filter by notification type
            status: Filter by status (unread, read, archived)
            priority: Filter by priority level
            unread_only: Show only unread notifications
            date_from: Start date for notification period
            date_to: End date for notification period
            limit: Maximum results to return
            
        Returns:
            Tuple of (notification list, summary metrics)
        """
        try:
            # Use secure query builder to prevent SQL injection
            builder = SecureQueryBuilder()
            builder.select([
                'n.id', 'n.user_id', 'n.company_id', 'n.notification_type',
                'n.priority', 'n.status', 'n.title', 'n.message', 'n.data',
                'n.created_at', 'n.read_at', 'n.expires_at', 'n.action_url',
                'n.category', 'u.full_name as user_name', 'c.name as company_name'
            ], 'notifications', 'n')
            
            builder.join('users u', 'n.user_id = u.id')
            builder.join('companies c', 'n.company_id = c.id')
            
            if user_id:
                builder.where('n.user_id', QueryOperator.EQUALS, user_id)
            
            if company_id:
                builder.where('n.company_id', QueryOperator.EQUALS, company_id)
            
            if notification_type:
                builder.where('n.notification_type', QueryOperator.EQUALS, notification_type)
            
            if status:
                builder.where('n.status', QueryOperator.EQUALS, status)
            elif unread_only:
                builder.where('n.status', QueryOperator.EQUALS, 'unread')
            
            if priority:
                builder.where('n.priority', QueryOperator.EQUALS, priority)
            
            if date_from:
                builder.where('n.created_at', QueryOperator.GREATER_EQUAL, date_from)
            
            if date_to:
                builder.where('n.created_at', QueryOperator.LESS_EQUAL, date_to)
            
            # Exclude expired notifications
            builder.where_raw('(n.expires_at IS NULL OR n.expires_at > NOW())', [])
            
            builder.order_by('n.priority', 'DESC')
            builder.order_by('n.created_at', 'DESC')
            builder.limit(limit)
            
            query, params = builder.build()
            results = execute_secure_query(self.db, query, params)
            
            notifications = []
            unread_count = 0
            priority_counts = {}
            
            for row in results:
                # Get delivery channels and retry count
                delivery_info = self._get_notification_delivery_info(row['id'])
                
                notification = NotificationInfo(
                    id=row['id'],
                    user_id=row['user_id'],
                    user_name=row['user_name'],
                    company_id=row['company_id'],
                    company_name=row['company_name'],
                    notification_type=row['notification_type'],
                    priority=row['priority'],
                    status=row['status'],
                    title=row['title'],
                    message=row['message'],
                    data=self._parse_notification_data(row['data']),
                    created_at=row['created_at'],
                    read_at=row['read_at'],
                    expires_at=row['expires_at'],
                    action_url=row['action_url'],
                    category=row['category'],
                    delivery_channels=delivery_info['channels'],
                    retry_count=delivery_info['retry_count']
                )
                notifications.append(notification)
                
                if notification.status == 'unread':
                    unread_count += 1
                
                priority = notification.priority
                priority_counts[priority] = priority_counts.get(priority, 0) + 1
            
            # Get summary statistics
            summary_stats = self._get_notification_summary_stats(user_id, company_id)
            
            metadata = {
                'total_notifications': len(notifications),
                'unread_count': unread_count,
                'priority_distribution': priority_counts,
                'summary_stats': summary_stats,
                'filters_applied': {
                    'user_id': user_id,
                    'company_id': company_id,
                    'notification_type': notification_type,
                    'status': status,
                    'unread_only': unread_only
                }
            }
            
            return notifications, metadata
            
        except (SecureQueryError, Exception) as e:
            logger.error(f"Error getting notifications", exc_info=True)
            return [], {'error': 'Failed to retrieve notifications', 'total_notifications': 0}
    
    @performance_tracked
    def create_notification(
        self,
        user_id: str,
        company_id: str,
        notification_type: str,
        priority: str,
        title: str,
        message: str,
        category: str = "general",
        data: Optional[Dict[str, Any]] = None,
        action_url: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        delivery_channels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create and send a new notification.
        
        Args:
            user_id: Target user ID
            company_id: Company context
            notification_type: Type of notification
            priority: Priority level
            title: Notification title
            message: Notification message
            category: Notification category
            data: Additional data payload
            action_url: URL for notification action
            expires_at: Expiration datetime
            delivery_channels: Channels to deliver notification
            
        Returns:
            Creation result with notification ID
        """
        try:
            # Generate notification ID
            cursor = self.db.cursor(dictionary=True)
            
            # Insert notification using secure query
            insert_query = """
                INSERT INTO notifications (
                    user_id, company_id, notification_type, priority, status,
                    title, message, category, data, action_url, expires_at,
                    created_at
                ) VALUES (%s, %s, %s, %s, 'unread', %s, %s, %s, %s, %s, %s, NOW())
            """
            
            # Validate and sanitize inputs
            if not user_id or not company_id:
                raise ValueError("user_id and company_id are required")
            
            cursor.execute(insert_query, (
                user_id, company_id, notification_type, priority,
                title[:255] if title else None,  # Limit title length
                message[:1000] if message else None,  # Limit message length
                category[:50] if category else None,  # Limit category length
                self._serialize_data(data) if data else None,
                action_url[:500] if action_url else None,  # Limit URL length
                expires_at
            ))
            
            notification_id = cursor.lastrowid or f"notif_{hash(f'{user_id}{title}{datetime.now()}') % 100000}"
            
            # Schedule delivery based on user preferences
            if delivery_channels is None:
                delivery_channels = self._get_default_delivery_channels(user_id)
            
            delivery_results = []
            for channel in delivery_channels:
                delivery_result = self._schedule_notification_delivery(
                    notification_id, user_id, channel, title, message
                )
                delivery_results.append(delivery_result)
            
            self.db.commit()
            
            return {
                'status': 'success',
                'notification_id': notification_id,
                'delivery_scheduled': len(delivery_channels),
                'delivery_results': delivery_results
            }
            
        except (SecureQueryError, ValueError, Exception) as e:
            self.db.rollback()
            logger.error(f"Error creating notification", exc_info=True)
            return {
                'status': 'error',
                'message': 'Failed to create notification'
            }
    
    @cached(ttl=300)  # 5-minute cache for alert rules
    @performance_tracked
    def get_alert_rules(
        self,
        company_id: Optional[str] = None,
        is_active: bool = True,
        alert_level: Optional[str] = None,
        condition_type: Optional[str] = None
    ) -> Tuple[List[AlertRule], Dict[str, Any]]:
        """
        Get alert rules and their configuration.
        
        Args:
            company_id: Filter by company
            is_active: Filter by active status
            alert_level: Filter by alert level
            condition_type: Filter by condition type
            
        Returns:
            Tuple of (alert rules list, configuration summary)
        """
        try:
            # Note: This assumes an alert_rules table exists
            # In practice, this might be configured in application settings
            
            # Simulate alert rules based on common supply chain scenarios
            alert_rules = []
            
            # Certificate expiry alerts
            cert_rule = AlertRule(
                id="rule_cert_expiry",
                name="Certificate Expiry Alert",
                description="Alert when certificates expire within 30 days",
                condition_type="threshold",
                conditions={
                    "table": "documents",
                    "field": "expiry_date",
                    "operator": "<=",
                    "threshold": 30,
                    "unit": "days"
                },
                alert_level="high",
                target_audience=["manager", "admin"],
                notification_template="cert_expiry",
                delivery_channels=["email", "in_app"],
                is_active=True,
                created_by="system",
                created_at=datetime.now() - timedelta(days=30),
                last_triggered=datetime.now() - timedelta(days=1),
                trigger_count=15
            )
            alert_rules.append(cert_rule)
            
            # Delivery delay alerts
            delivery_rule = AlertRule(
                id="rule_delivery_delay",
                name="Delivery Delay Alert",
                description="Alert when deliveries are overdue",
                condition_type="threshold",
                conditions={
                    "table": "purchase_orders",
                    "field": "delivery_date",
                    "operator": "<",
                    "threshold": 0,
                    "unit": "days"
                },
                alert_level="urgent",
                target_audience=["buyer", "seller", "manager"],
                notification_template="delivery_delay",
                delivery_channels=["email", "in_app", "sms"],
                is_active=True,
                created_by="system",
                created_at=datetime.now() - timedelta(days=20),
                last_triggered=datetime.now() - timedelta(hours=6),
                trigger_count=8
            )
            alert_rules.append(delivery_rule)
            
            # Low inventory alerts
            inventory_rule = AlertRule(
                id="rule_low_inventory",
                name="Low Inventory Alert",
                description="Alert when inventory falls below threshold",
                condition_type="threshold",
                conditions={
                    "table": "batches",
                    "field": "quantity",
                    "operator": "<",
                    "threshold": 10,
                    "unit": "MT"
                },
                alert_level="medium",
                target_audience=["operator", "manager"],
                notification_template="low_inventory",
                delivery_channels=["in_app"],
                is_active=True,
                created_by="system",
                created_at=datetime.now() - timedelta(days=45),
                last_triggered=datetime.now() - timedelta(days=3),
                trigger_count=22
            )
            alert_rules.append(inventory_rule)
            
            # Transparency score alerts
            transparency_rule = AlertRule(
                id="rule_transparency_low",
                name="Low Transparency Score Alert",
                description="Alert when batch transparency score is below threshold",
                condition_type="threshold",
                conditions={
                    "table": "batches",
                    "field": "transparency_score",
                    "operator": "<",
                    "threshold": 70,
                    "unit": "percent"
                },
                alert_level="medium",
                target_audience=["manager"],
                notification_template="low_transparency",
                delivery_channels=["email", "in_app"],
                is_active=True,
                created_by="system",
                created_at=datetime.now() - timedelta(days=60),
                last_triggered=datetime.now() - timedelta(hours=18),
                trigger_count=35
            )
            alert_rules.append(transparency_rule)
            
            # Apply filters
            filtered_rules = alert_rules
            if not is_active:
                filtered_rules = [r for r in filtered_rules if not r.is_active]
            if alert_level:
                filtered_rules = [r for r in filtered_rules if r.alert_level == alert_level]
            if condition_type:
                filtered_rules = [r for r in filtered_rules if r.condition_type == condition_type]
            
            # Generate summary
            total_triggers = sum(r.trigger_count for r in filtered_rules)
            active_rules = len([r for r in filtered_rules if r.is_active])
            
            metadata = {
                'total_rules': len(filtered_rules),
                'active_rules': active_rules,
                'total_triggers_all_time': total_triggers,
                'alert_level_distribution': {
                    level: len([r for r in filtered_rules if r.alert_level == level])
                    for level in ['low', 'medium', 'high', 'urgent']
                },
                'most_triggered_rule': max(filtered_rules, key=lambda r: r.trigger_count).name if filtered_rules else None
            }
            
            return filtered_rules, metadata
            
        except Exception as e:
            logger.error(f"Error getting alert rules: {str(e)}")
            return [], {'error': str(e), 'total_rules': 0}
    
    @performance_tracked
    def mark_notification_read(
        self,
        notification_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Mark a notification as read.
        
        Args:
            notification_id: Notification to mark as read
            user_id: User marking the notification
            
        Returns:
            Operation result
        """
        try:
            cursor = self.db.cursor()
            
            # Update notification status
            update_query = """
                UPDATE notifications 
                SET status = 'read', read_at = NOW()
                WHERE id = %s AND user_id = %s AND status = 'unread'
            """
            
            cursor.execute(update_query, (notification_id, user_id))
            rows_affected = cursor.rowcount
            
            self.db.commit()
            
            if rows_affected > 0:
                return {
                    'status': 'success',
                    'message': 'Notification marked as read'
                }
            else:
                return {
                    'status': 'not_found',
                    'message': 'Notification not found or already read'
                }
                
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error marking notification as read: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    @cached(ttl=600)  # 10-minute cache for preferences
    @performance_tracked
    def get_notification_preferences(
        self,
        user_id: str
    ) -> Tuple[NotificationPreferences, Dict[str, Any]]:
        """
        Get user notification preferences.
        
        Args:
            user_id: User ID to get preferences for
            
        Returns:
            Tuple of (preferences object, metadata)
        """
        try:
            cursor = self.db.cursor(dictionary=True)
            
            # Get user preferences
            query = """
                SELECT 
                    user_id, email_notifications, sms_notifications,
                    in_app_notifications, webhook_notifications, digest_frequency,
                    categories_enabled, quiet_hours_start, quiet_hours_end,
                    timezone
                FROM user_notification_preferences
                WHERE user_id = %s
            """
            
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            
            if result:
                preferences = NotificationPreferences(
                    user_id=result['user_id'],
                    email_notifications=result['email_notifications'],
                    sms_notifications=result['sms_notifications'],
                    in_app_notifications=result['in_app_notifications'],
                    webhook_notifications=result['webhook_notifications'],
                    digest_frequency=result['digest_frequency'],
                    categories_enabled=self._parse_categories(result['categories_enabled']),
                    quiet_hours_start=result['quiet_hours_start'],
                    quiet_hours_end=result['quiet_hours_end'],
                    timezone=result['timezone']
                )
            else:
                # Default preferences if none exist
                preferences = NotificationPreferences(
                    user_id=user_id,
                    email_notifications=True,
                    sms_notifications=False,
                    in_app_notifications=True,
                    webhook_notifications=False,
                    digest_frequency='immediate',
                    categories_enabled=['alert', 'reminder', 'update'],
                    quiet_hours_start=None,
                    quiet_hours_end=None,
                    timezone='UTC'
                )
            
            metadata = {
                'has_custom_preferences': result is not None,
                'delivery_channels_enabled': sum([
                    preferences.email_notifications,
                    preferences.sms_notifications,
                    preferences.in_app_notifications,
                    preferences.webhook_notifications
                ])
            }
            
            return preferences, metadata
            
        except Exception as e:
            logger.error(f"Error getting notification preferences: {str(e)}")
            # Return default preferences on error
            default_prefs = NotificationPreferences(
                user_id=user_id,
                email_notifications=True,
                sms_notifications=False,
                in_app_notifications=True,
                webhook_notifications=False,
                digest_frequency='immediate',
                categories_enabled=['alert'],
                quiet_hours_start=None,
                quiet_hours_end=None,
                timezone='UTC'
            )
            return default_prefs, {'error': str(e)}
    
    @performance_tracked
    def trigger_alert_check(
        self,
        alert_rule_id: str,
        force_trigger: bool = False
    ) -> Dict[str, Any]:
        """
        Trigger an alert rule check and create notifications if conditions are met.
        
        Args:
            alert_rule_id: Alert rule to check
            force_trigger: Force trigger regardless of conditions
            
        Returns:
            Alert check result
        """
        try:
            # Get alert rule
            alert_rules, _ = self.get_alert_rules()
            alert_rule = next((r for r in alert_rules if r.id == alert_rule_id), None)
            
            if not alert_rule:
                return {
                    'status': 'error',
                    'message': 'Alert rule not found'
                }
            
            if not alert_rule.is_active and not force_trigger:
                return {
                    'status': 'skipped',
                    'message': 'Alert rule is inactive'
                }
            
            # Check alert conditions
            conditions_met = self._check_alert_conditions(alert_rule.conditions)
            
            if not conditions_met and not force_trigger:
                return {
                    'status': 'no_action',
                    'message': 'Alert conditions not met'
                }
            
            # Get affected items
            affected_items = self._get_affected_items(alert_rule.conditions)
            
            # Create notifications for target audience
            notifications_created = []
            for target in alert_rule.target_audience:
                # Get users matching target criteria
                target_users = self._get_users_by_criteria(target)
                
                for user in target_users:
                    notification_result = self.create_notification(
                        user_id=user['id'],
                        company_id=user['company_id'],
                        notification_type='alert',
                        priority=alert_rule.alert_level,
                        title=f"Alert: {alert_rule.name}",
                        message=self._generate_alert_message(alert_rule, affected_items),
                        category='alert',
                        data={
                            'alert_rule_id': alert_rule_id,
                            'affected_items': affected_items,
                            'trigger_timestamp': datetime.now().isoformat()
                        },
                        delivery_channels=alert_rule.delivery_channels
                    )
                    notifications_created.append(notification_result)
            
            return {
                'status': 'success',
                'alert_rule': alert_rule.name,
                'conditions_met': conditions_met,
                'affected_items_count': len(affected_items),
                'notifications_created': len(notifications_created),
                'force_triggered': force_trigger
            }
            
        except Exception as e:
            logger.error(f"Error triggering alert check: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    # Helper methods
    
    def _get_notification_delivery_info(self, notification_id: str) -> Dict[str, Any]:
        """Get delivery channel and retry information for a notification."""
        try:
            cursor = self.db.cursor(dictionary=True)
            cursor.execute("""
                SELECT delivery_channel, retry_count
                FROM notification_deliveries
                WHERE notification_id = %s
            """, (notification_id,))
            
            results = cursor.fetchall()
            channels = [r['delivery_channel'] for r in results]
            max_retry = max([r['retry_count'] for r in results], default=0)
            
            return {
                'channels': channels,
                'retry_count': max_retry
            }
            
        except Exception:
            return {'channels': ['in_app'], 'retry_count': 0}
    
    def _parse_notification_data(self, data_string: Optional[str]) -> Dict[str, Any]:
        """Parse notification data from stored string."""
        if not data_string:
            return {}
        
        try:
            import json
            return json.loads(data_string)
        except Exception:
            return {'raw_data': data_string}
    
    def _serialize_data(self, data: Dict[str, Any]) -> str:
        """Serialize notification data for storage."""
        try:
            import json
            return json.dumps(data, default=str)
        except Exception:
            return str(data)
    
    def _get_notification_summary_stats(self, user_id: Optional[str], company_id: Optional[str]) -> Dict[str, Any]:
        """Get summary statistics for notifications."""
        try:
            cursor = self.db.cursor(dictionary=True)
            
            base_conditions = []
            params = []
            
            if user_id:
                base_conditions.append("user_id = %s")
                params.append(user_id)
            if company_id:
                base_conditions.append("company_id = %s")
                params.append(company_id)
            
            where_clause = "WHERE " + " AND ".join(base_conditions) if base_conditions else ""
            
            # Get counts by status
            query = f"""
                SELECT 
                    status,
                    COUNT(*) as count,
                    COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR) THEN 1 END) as count_24h
                FROM notifications 
                {where_clause}
                GROUP BY status
            """
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            status_counts = {r['status']: r['count'] for r in results}
            status_24h = {r['status']: r['count_24h'] for r in results}
            
            return {
                'total_all_time': sum(status_counts.values()),
                'total_24h': sum(status_24h.values()),
                'by_status': status_counts,
                'by_status_24h': status_24h
            }
            
        except Exception:
            return {'total_all_time': 0, 'total_24h': 0}
    
    def _get_default_delivery_channels(self, user_id: str) -> List[str]:
        """Get default delivery channels for a user."""
        preferences, _ = self.get_notification_preferences(user_id)
        
        channels = []
        if preferences.in_app_notifications:
            channels.append('in_app')
        if preferences.email_notifications:
            channels.append('email')
        if preferences.sms_notifications:
            channels.append('sms')
        if preferences.webhook_notifications:
            channels.append('webhook')
        
        return channels or ['in_app']  # Default to in-app if no preferences
    
    def _schedule_notification_delivery(
        self, 
        notification_id: str, 
        user_id: str, 
        channel: str, 
        title: str, 
        message: str
    ) -> Dict[str, Any]:
        """Schedule notification delivery for a specific channel."""
        try:
            # Get delivery address based on channel
            delivery_address = self._get_delivery_address(user_id, channel)
            
            # Insert delivery record
            cursor = self.db.cursor()
            cursor.execute("""
                INSERT INTO notification_deliveries (
                    notification_id, delivery_channel, delivery_status,
                    delivery_address, retry_count, created_at
                ) VALUES (%s, %s, 'pending', %s, 0, NOW())
            """, (notification_id, channel, delivery_address))
            
            # Simulate immediate delivery for in-app notifications
            if channel == 'in_app':
                cursor.execute("""
                    UPDATE notification_deliveries 
                    SET delivery_status = 'delivered', delivered_at = NOW()
                    WHERE notification_id = %s AND delivery_channel = %s
                """, (notification_id, channel))
            
            return {
                'channel': channel,
                'status': 'scheduled',
                'delivery_address': delivery_address
            }
            
        except Exception as e:
            logger.error(f"Error scheduling notification delivery: {str(e)}")
            return {
                'channel': channel,
                'status': 'failed',
                'error': str(e)
            }
    
    def _get_delivery_address(self, user_id: str, channel: str) -> str:
        """Get delivery address for user and channel."""
        try:
            cursor = self.db.cursor(dictionary=True)
            
            if channel == 'email':
                cursor.execute("SELECT email FROM users WHERE id = %s", (user_id,))
                result = cursor.fetchone()
                return result['email'] if result else 'no-email@example.com'
            elif channel == 'sms':
                cursor.execute("SELECT phone FROM users WHERE id = %s", (user_id,))
                result = cursor.fetchone()
                return result['phone'] if result else 'no-phone'
            elif channel == 'webhook':
                # Would get webhook URL from user preferences
                return f'webhook://api.company.com/notifications/{user_id}'
            else:  # in_app
                return 'in_app'
                
        except Exception:
            return f'{channel}_fallback'
    
    def _parse_categories(self, categories_string: Optional[str]) -> List[str]:
        """Parse enabled categories from string."""
        if not categories_string:
            return ['alert', 'reminder']
        
        try:
            import json
            return json.loads(categories_string)
        except Exception:
            return categories_string.split(',') if categories_string else []
    
    def _check_alert_conditions(self, conditions: Dict[str, Any]) -> bool:
        """Check if alert conditions are met."""
        # Simplified condition checking - would implement full rules engine
        try:
            table = conditions.get('table')
            field = conditions.get('field')
            operator = conditions.get('operator')
            threshold = conditions.get('threshold')
            
            if table == 'documents' and field == 'expiry_date':
                # Check for expiring certificates
                cursor = self.db.cursor()
                cursor.execute("""
                    SELECT COUNT(*) as count FROM documents 
                    WHERE expiry_date <= DATE_ADD(NOW(), INTERVAL %s DAY)
                    AND document_category = 'certificate'
                """, (threshold,))
                result = cursor.fetchone()
                return result[0] > 0 if result else False
            
            # Add more condition types as needed
            return False
            
        except Exception:
            return False
    
    def _get_affected_items(self, conditions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get items affected by alert conditions."""
        # Return simplified affected items list
        return [
            {
                'id': 'item_001',
                'type': conditions.get('table', 'unknown'),
                'description': f"Item meeting {conditions.get('field')} condition"
            }
        ]
    
    def _get_users_by_criteria(self, criteria: str) -> List[Dict[str, str]]:
        """Get users matching criteria (role, company, etc.)."""
        try:
            cursor = self.db.cursor(dictionary=True)
            
            # Simple role-based targeting
            if criteria in ['admin', 'manager', 'operator', 'viewer']:
                cursor.execute("""
                    SELECT id, company_id, full_name, email 
                    FROM users 
                    WHERE role = %s AND is_active = TRUE
                    LIMIT 10
                """, (criteria,))
                return cursor.fetchall()
            
            return []
            
        except Exception:
            return []
    
    def _generate_alert_message(self, alert_rule: AlertRule, affected_items: List[Dict[str, Any]]) -> str:
        """Generate alert message based on rule and affected items."""
        item_count = len(affected_items)
        
        if alert_rule.id == 'rule_cert_expiry':
            return f"{item_count} certificates are expiring within 30 days. Please review and initiate renewal process."
        elif alert_rule.id == 'rule_delivery_delay':
            return f"{item_count} deliveries are overdue. Immediate attention required to prevent customer impact."
        elif alert_rule.id == 'rule_low_inventory':
            return f"{item_count} inventory items are below minimum threshold. Consider replenishment orders."
        else:
            return f"Alert condition met: {alert_rule.description}. {item_count} items affected."

# Convenience functions

def create_notification_manager(db_connection) -> NotificationManager:
    """Create notification manager instance."""
    return NotificationManager(db_connection)

def send_urgent_alert(
    db_connection, 
    user_id: str, 
    company_id: str, 
    title: str, 
    message: str
) -> Dict[str, Any]:
    """Quick function to send urgent alert."""
    manager = NotificationManager(db_connection)
    return manager.create_notification(
        user_id=user_id,
        company_id=company_id,
        notification_type='alert',
        priority='urgent',
        title=title,
        message=message,
        category='alert',
        delivery_channels=['email', 'in_app', 'sms']
    )

def get_unread_count(db_connection, user_id: str) -> int:
    """Quick function to get unread notification count."""
    manager = NotificationManager(db_connection)
    notifications, metadata = manager.get_notifications(
        user_id=user_id,
        unread_only=True,
        limit=100
    )
    return metadata.get('unread_count', 0)
