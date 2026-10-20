"""
Email service providers - SMTP, SendGrid, Resend, AWS SES
"""
import os
import smtplib
import asyncio
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formataddr
from typing import Dict, Optional, List
from datetime import datetime
from pathlib import Path


class BaseEmailProvider:
    """Base class for email providers"""
    
    def __init__(self):
        self.daily_sent_count = 0
        self.hourly_sent_count = 0
        self.last_email_time = None
    
    async def send_email(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        html_body: str,
        text_body: str,
        from_email: str,
        from_name: str,
        tracking_id: Optional[str] = None,
        attachments: Optional[List[str]] = None
    ) -> Dict:
        """Send email - to be implemented by subclasses"""
        raise NotImplementedError
    
    async def _add_tracking_pixel(self, html_body: str, tracking_id: str) -> str:
        """Add tracking pixel to HTML"""
        app_url = os.getenv('APP_URL', 'http://localhost:8000')
        # Remove trailing slash from app_url if present
        app_url = app_url.rstrip('/')
        pixel = f'<img src="{app_url}/track/open/{tracking_id}" width="1" height="1" alt="" />'
        return html_body + pixel
    
    async def _rate_limit_delay(self):
        """Add human-like delay between emails"""
        min_delay = int(os.getenv('MIN_EMAIL_DELAY', 60))
        max_delay = int(os.getenv('MAX_EMAIL_DELAY', 180))
        delay = random.uniform(min_delay, max_delay)
        
        print(f"[EmailProvider] Waiting {delay:.1f}s before next email...")
        await asyncio.sleep(delay)


class SMTPProvider(BaseEmailProvider):
    """SMTP email provider (Gmail, Outlook, etc.)"""
    
    def __init__(self):
        super().__init__()
        self.host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.port = int(os.getenv('SMTP_PORT', 587))
        self.username = os.getenv('SMTP_USERNAME')
        self.password = os.getenv('SMTP_PASSWORD')
        self.use_tls = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
        
        # FROM_EMAIL defaults to SMTP_USERNAME (same for Gmail, Outlook, etc.)
        self.default_from_email = os.getenv('FROM_EMAIL', self.username)
        self.default_from_name = os.getenv('FROM_NAME', 'Job Seeker')
    
    async def send_email(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        html_body: str,
        text_body: str,
        from_email: str,
        from_name: str,
        tracking_id: Optional[str] = None,
        attachments: Optional[List[str]] = None
    ) -> Dict:
        """Send email via SMTP with optional attachments"""
        
        try:
            # Rate limiting
            if self.last_email_time:
                await self._rate_limit_delay()
            
            # Add tracking if enabled
            if tracking_id and os.getenv('TRACK_OPENS', 'true').lower() == 'true':
                html_body = await self._add_tracking_pixel(html_body, tracking_id)
            
            # Create message
            msg = MIMEMultipart('mixed')  # Changed to 'mixed' to support attachments
            msg['Subject'] = subject
            msg['From'] = formataddr((from_name, from_email))
            msg['To'] = formataddr((to_name, to_email))
            
            # Create alternative part for text/html
            msg_alternative = MIMEMultipart('alternative')
            msg.attach(msg_alternative)
            
            # Attach text and HTML parts
            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(html_body, 'html')
            msg_alternative.attach(part1)
            msg_alternative.attach(part2)
            
            # Attach files (resume, cover letter, etc.)
            if attachments:
                for file_path in attachments:
                    if not os.path.exists(file_path):
                        print(f"[SMTP] Warning: Attachment not found: {file_path}")
                        continue
                    
                    with open(file_path, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                    
                    encoders.encode_base64(part)
                    filename = Path(file_path).name
                    part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                    msg.attach(part)
                    
                    print(f"[SMTP] Attached: {filename}")
            
            # Send
            with smtplib.SMTP(self.host, self.port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            self.last_email_time = datetime.now()
            self.daily_sent_count += 1
            self.hourly_sent_count += 1
            
            print(f"[SMTP] Sent email to {to_email}")
            
            return {
                'success': True,
                'message_id': msg.get('Message-ID'),
                'sent_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"[SMTP] Error sending to {to_email}: {e}")
            return {
                'success': False,
                'error': str(e)
            }


def get_email_provider(provider_name: str = None) -> BaseEmailProvider:
    """Get email provider instance"""
    
    if not provider_name:
        provider_name = os.getenv('EMAIL_PROVIDER', 'smtp')
    
    if provider_name.lower() == 'smtp':
        return SMTPProvider()
    else:
        # Default to SMTP
        return SMTPProvider()
