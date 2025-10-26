"""
Notification service for sending alerts via multiple channels
Supports Email (SendGrid), SMS/WhatsApp (Twilio), and Push (Firebase)
"""

import os
from typing import Dict, Any, Optional, List
from enum import Enum
import asyncio
import logging
from dataclasses import dataclass

# Conditional imports - these will only work if packages are installed
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False

from app.core.metrics import track_notification_sent

logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    """Supported notification channels"""
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    PUSH = "push"
    IN_APP = "in_app"


@dataclass
class NotificationConfig:
    """Configuration for notification services"""
    # SendGrid
    sendgrid_api_key: Optional[str] = None
    sendgrid_from_email: Optional[str] = None
    
    # Twilio
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None
    twilio_whatsapp_number: Optional[str] = None
    
    # Firebase
    firebase_credentials_path: Optional[str] = None
    
    def __post_init__(self):
        """Load configuration from environment variables"""
        self.sendgrid_api_key = os.getenv('SENDGRID_API_KEY', self.sendgrid_api_key)
        self.sendgrid_from_email = os.getenv('SENDGRID_FROM_EMAIL', self.sendgrid_from_email or 'noreply@cumpair.com')
        
        self.twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID', self.twilio_account_sid)
        self.twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN', self.twilio_auth_token)
        self.twilio_phone_number = os.getenv('TWILIO_PHONE_NUMBER', self.twilio_phone_number)
        self.twilio_whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER', self.twilio_whatsapp_number or 'whatsapp:+14155238886')
        
        self.firebase_credentials_path = os.getenv('FIREBASE_CREDENTIALS_PATH', self.firebase_credentials_path)


class NotificationService:
    """
    Unified notification service supporting multiple channels
    """
    
    def __init__(self, config: Optional[NotificationConfig] = None):
        self.config = config or NotificationConfig()
        self._sendgrid_client = None
        self._twilio_client = None
        self._firebase_initialized = False
        
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize notification service clients"""
        # SendGrid
        if SENDGRID_AVAILABLE and self.config.sendgrid_api_key:
            try:
                self._sendgrid_client = SendGridAPIClient(self.config.sendgrid_api_key)
                logger.info("SendGrid client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize SendGrid: {e}")
        
        # Twilio
        if TWILIO_AVAILABLE and self.config.twilio_account_sid and self.config.twilio_auth_token:
            try:
                self._twilio_client = TwilioClient(
                    self.config.twilio_account_sid,
                    self.config.twilio_auth_token
                )
                logger.info("Twilio client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio: {e}")
        
        # Firebase
        if FIREBASE_AVAILABLE and self.config.firebase_credentials_path:
            try:
                if not self._firebase_initialized:
                    cred = credentials.Certificate(self.config.firebase_credentials_path)
                    firebase_admin.initialize_app(cred)
                    self._firebase_initialized = True
                    logger.info("Firebase initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Firebase: {e}")
    
    async def send_notification(self, notification_id: int) -> Dict[str, Any]:
        """
        Send notification by ID (loads from database)
        
        Args:
            notification_id: Database ID of the notification
            
        Returns:
            Result dictionary with status and details
        """
        try:
            # Import here to avoid circular imports
            from app.core.database import async_session_maker
            from app.models.alerts import Notification
            from sqlalchemy import select
            
            async with async_session_maker() as session:
                stmt = select(Notification).where(Notification.id == notification_id)
                result = await session.execute(stmt)
                notification = result.scalar_one_or_none()
                
                if not notification:
                    logger.error(f"Notification {notification_id} not found")
                    return {'status': 'error', 'message': 'Notification not found'}
                
                # Send via appropriate channel
                channel = NotificationChannel(notification.channel)
                
                if channel == NotificationChannel.EMAIL:
                    result = await self.send_email(
                        to_email=notification.recipient,
                        subject=notification.title,
                        body=notification.message,
                        html_content=notification.metadata.get('html_content')
                    )
                elif channel == NotificationChannel.SMS:
                    result = await self.send_sms(
                        to_number=notification.recipient,
                        message=notification.message
                    )
                elif channel == NotificationChannel.WHATSAPP:
                    result = await self.send_whatsapp(
                        to_number=notification.recipient,
                        message=notification.message
                    )
                elif channel == NotificationChannel.PUSH:
                    result = await self.send_push(
                        device_token=notification.recipient,
                        title=notification.title,
                        body=notification.message,
                        data=notification.metadata.get('data', {})
                    )
                else:
                    result = {'status': 'skipped', 'message': 'In-app notification (no external send)'}
                
                # Update notification status
                notification.status = 'sent' if result.get('status') == 'success' else 'failed'
                notification.sent_at = asyncio.get_event_loop().time()
                await session.commit()
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to send notification {notification_id}: {e}")
            track_notification_sent(channel='error', status='failed')
            return {'status': 'error', 'message': str(e)}
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send email via SendGrid
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Plain text body
            html_content: Optional HTML body
            
        Returns:
            Result dictionary
        """
        if not SENDGRID_AVAILABLE or not self._sendgrid_client:
            logger.warning("SendGrid not available or not configured")
            track_notification_sent('email', 'skipped')
            return {'status': 'skipped', 'message': 'SendGrid not configured'}
        
        try:
            message = Mail(
                from_email=self.config.sendgrid_from_email,
                to_emails=to_email,
                subject=subject,
                plain_text_content=body,
                html_content=html_content or f"<p>{body}</p>"
            )
            
            response = self._sendgrid_client.send(message)
            
            track_notification_sent('email', 'success')
            logger.info(f"Email sent to {to_email} successfully")
            
            return {
                'status': 'success',
                'channel': 'email',
                'recipient': to_email,
                'response_code': response.status_code
            }
            
        except Exception as e:
            track_notification_sent('email', 'failed')
            logger.error(f"Failed to send email to {to_email}: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def send_sms(self, to_number: str, message: str) -> Dict[str, Any]:
        """
        Send SMS via Twilio
        
        Args:
            to_number: Recipient phone number (E.164 format)
            message: SMS message body
            
        Returns:
            Result dictionary
        """
        if not TWILIO_AVAILABLE or not self._twilio_client:
            logger.warning("Twilio not available or not configured")
            track_notification_sent('sms', 'skipped')
            return {'status': 'skipped', 'message': 'Twilio not configured'}
        
        try:
            message_obj = self._twilio_client.messages.create(
                body=message,
                from_=self.config.twilio_phone_number,
                to=to_number
            )
            
            track_notification_sent('sms', 'success')
            logger.info(f"SMS sent to {to_number} successfully")
            
            return {
                'status': 'success',
                'channel': 'sms',
                'recipient': to_number,
                'message_sid': message_obj.sid
            }
            
        except Exception as e:
            track_notification_sent('sms', 'failed')
            logger.error(f"Failed to send SMS to {to_number}: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def send_whatsapp(self, to_number: str, message: str) -> Dict[str, Any]:
        """
        Send WhatsApp message via Twilio
        
        Args:
            to_number: Recipient WhatsApp number (format: whatsapp:+1234567890)
            message: WhatsApp message body
            
        Returns:
            Result dictionary
        """
        if not TWILIO_AVAILABLE or not self._twilio_client:
            logger.warning("Twilio not available or not configured")
            track_notification_sent('whatsapp', 'skipped')
            return {'status': 'skipped', 'message': 'Twilio not configured'}
        
        try:
            # Ensure number has whatsapp: prefix
            if not to_number.startswith('whatsapp:'):
                to_number = f'whatsapp:{to_number}'
            
            message_obj = self._twilio_client.messages.create(
                body=message,
                from_=self.config.twilio_whatsapp_number,
                to=to_number
            )
            
            track_notification_sent('whatsapp', 'success')
            logger.info(f"WhatsApp message sent to {to_number} successfully")
            
            return {
                'status': 'success',
                'channel': 'whatsapp',
                'recipient': to_number,
                'message_sid': message_obj.sid
            }
            
        except Exception as e:
            track_notification_sent('whatsapp', 'failed')
            logger.error(f"Failed to send WhatsApp to {to_number}: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def send_push(
        self,
        device_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Send push notification via Firebase Cloud Messaging
        
        Args:
            device_token: FCM device registration token
            title: Notification title
            body: Notification body
            data: Optional data payload
            
        Returns:
            Result dictionary
        """
        if not FIREBASE_AVAILABLE or not self._firebase_initialized:
            logger.warning("Firebase not available or not configured")
            track_notification_sent('push', 'skipped')
            return {'status': 'skipped', 'message': 'Firebase not configured'}
        
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                token=device_token
            )
            
            response = messaging.send(message)
            
            track_notification_sent('push', 'success')
            logger.info(f"Push notification sent successfully: {response}")
            
            return {
                'status': 'success',
                'channel': 'push',
                'response': response
            }
            
        except Exception as e:
            track_notification_sent('push', 'failed')
            logger.error(f"Failed to send push notification: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def send_bulk_notifications(
        self,
        notifications: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Send multiple notifications in parallel
        
        Args:
            notifications: List of notification dictionaries with 'channel', 'recipient', etc.
            
        Returns:
            List of result dictionaries
        """
        tasks = []
        
        for notif in notifications:
            channel = NotificationChannel(notif['channel'])
            
            if channel == NotificationChannel.EMAIL:
                task = self.send_email(
                    notif['recipient'],
                    notif.get('subject', 'Notification'),
                    notif['message']
                )
            elif channel == NotificationChannel.SMS:
                task = self.send_sms(notif['recipient'], notif['message'])
            elif channel == NotificationChannel.WHATSAPP:
                task = self.send_whatsapp(notif['recipient'], notif['message'])
            elif channel == NotificationChannel.PUSH:
                task = self.send_push(
                    notif['recipient'],
                    notif.get('title', 'Notification'),
                    notif['message']
                )
            else:
                continue
            
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return [
            r if isinstance(r, dict) else {'status': 'error', 'message': str(r)}
            for r in results
        ]


# Global notification service instance
notification_service = NotificationService()
