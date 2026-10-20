"""
Email Dispatcher - Orchestrates email sending campaigns
"""
import os
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict
from sqlalchemy.orm import Session

from app.outreach.providers import get_email_provider
from app.outreach.message_generator import EmailMessageGenerator
from app.outreach.models import EmailCampaign, EmailOutreach, EmailEvent
from app.models.contact import Contact
from app.models import Company


class EmailDispatcher:
    """Main email dispatcher orchestrator"""
    
    def __init__(self, db: Session):
        self.db = db
        self.provider = get_email_provider()
        self.message_gen = EmailMessageGenerator()
        
        self.daily_limit = int(os.getenv('MAX_DAILY_EMAILS', 50))
        self.hourly_limit = int(os.getenv('MAX_HOURLY_EMAILS', 10))
    
    async def send_campaign_batch(self, campaign_id: int, batch_size: int = 10, require_approval: bool = False) -> Dict:
        """Send a batch of emails for a campaign with optional manual approval"""
        
        campaign = self.db.query(EmailCampaign).filter(
            EmailCampaign.id == campaign_id
        ).first()
        
        if not campaign:
            return {'error': 'Campaign not found'}
        
        # Get queued emails
        queued_emails = self.db.query(EmailOutreach).filter(
            EmailOutreach.campaign_id == campaign_id,
            EmailOutreach.status == 'queued'
        ).limit(batch_size).all()
        
        print(f"\n[EmailDispatcher] Sending batch for campaign: {campaign.name}")
        print(f"[EmailDispatcher] {len(queued_emails)} emails to send")
        
        # Manual approval flow
        if require_approval and len(queued_emails) > 0:
            print("\n" + "=" * 60)
            print("📧 MANUAL APPROVAL REQUIRED")
            print("=" * 60)
            print(f"\nAbout to send {len(queued_emails)} emails:\n")
            
            for i, outreach in enumerate(queued_emails[:5], 1):  # Show first 5
                contact = self.db.query(Contact).filter(
                    Contact.id == outreach.contact_id
                ).first()
                
                company = self.db.query(Company).filter(
                    Company.id == contact.company_id
                ).first() if contact else None
                
                print(f"{i}. To: {outreach.recipient_name} <{outreach.recipient_email}>")
                print(f"   Company: {company.name if company else 'Unknown'}")
                print(f"   Subject: {outreach.subject_line}")
                if outreach.personalization and outreach.personalization.get('attachments'):
                    attachments = outreach.personalization['attachments']
                    print(f"   Attachments: {', '.join([os.path.basename(a) for a in attachments])}")
                print()
            
            if len(queued_emails) > 5:
                print(f"... and {len(queued_emails) - 5} more\n")
            
            print("=" * 60)
            approval = input("\n✋ Send these emails? (yes/no): ").strip().lower()
            
            if approval not in ['yes', 'y']:
                print("\n❌ Sending cancelled by user")
                return {
                    'sent': 0,
                    'failed': 0,
                    'cancelled': True,
                    'errors': []
                }
            
            print("\n✅ Approved! Sending emails...\n")
        
        results = {
            'sent': 0,
            'failed': 0,
            'errors': []
        }
        
        for outreach in queued_emails:
            try:
                # Check daily/hourly limits
                if not self._check_limits():
                    print(f"[EmailDispatcher] Daily/hourly limit reached")
                    break
                
                # Get contact details
                contact = self.db.query(Contact).filter(
                    Contact.id == outreach.contact_id
                ).first()
                
                if not contact:
                    outreach.status = 'failed'
                    outreach.error_message = 'Contact not found'
                    results['failed'] += 1
                    continue
                
                # Send email
                result = await self.provider.send_email(
                    to_email=outreach.recipient_email,
                    to_name=outreach.recipient_name or contact.name or 'Recruiter',
                    subject=outreach.subject_line,
                    html_body=outreach.email_body_html,
                    text_body=outreach.email_body_text,
                    from_email=self.provider.default_from_email,
                    from_name=self.provider.default_from_name,
                    tracking_id=str(outreach.id),
                    attachments=outreach.personalization.get('attachments') if outreach.personalization else None
                )
                
                if result['success']:
                    # Update outreach record
                    outreach.status = 'sent'
                    outreach.sent_at = datetime.now()
                    outreach.message_id = result.get('message_id')
                    
                    # Log event
                    event = EmailEvent(
                        outreach_id=outreach.id,
                        event_type='sent',
                        event_data={'message_id': result.get('message_id')}
                    )
                    self.db.add(event)
                    
                    # Update campaign stats
                    campaign.emails_sent += 1
                    
                    results['sent'] += 1
                    print(f"[EmailDispatcher] Sent to {outreach.recipient_email}")
                
                else:
                    outreach.status = 'failed'
                    outreach.error_message = result.get('error')
                    results['failed'] += 1
                    results['errors'].append({
                        'email': outreach.recipient_email,
                        'error': result.get('error')
                    })
                
                self.db.commit()
                
            except Exception as e:
                print(f"[EmailDispatcher] Error: {e}")
                outreach.status = 'failed'
                outreach.error_message = str(e)
                results['failed'] += 1
                self.db.commit()
        
        return results


    
    async def create_campaign_from_contacts(
        self,
        name: str,
        contact_ids: List[int],
        your_profile: Dict,
        template_type: str = 'cold_outreach',
        attachments: List[str] = None
    ) -> int:
        """Create email campaign from list of contacts with optional attachments"""
        
        print(f"\n[EmailDispatcher] Creating campaign: {name}")
        
        # Validate attachments exist
        if attachments:
            for file_path in attachments:
                if not os.path.exists(file_path):
                    print(f"[WARNING] Attachment not found: {file_path}")
                else:
                    print(f"[INFO] Will attach: {os.path.basename(file_path)}")
        
        # Create campaign
        campaign = EmailCampaign(
            name=name,
            template_type=template_type,
            status='active',
            total_contacts=len(contact_ids)
        )
        self.db.add(campaign)
        self.db.flush()
        
        # Generate emails for each contact
        generated_count = 0
        for contact_id in contact_ids:
            contact = self.db.query(Contact).filter(
                Contact.id == contact_id
            ).first()
            
            if not contact:
                continue
            
            # Get company info
            company = self.db.query(Company).filter(
                Company.id == contact.company_id
            ).first()
            
            # Generate personalized email
            contact_data = {
                'name': contact.name,
                'title': contact.title,
                'company': company.name if company else 'the company'
            }
            
            email_content = await self.message_gen.generate_cold_outreach(
                contact=contact_data,
                your_profile=your_profile
            )
            
            # Create outreach record
            outreach = EmailOutreach(
                campaign_id=campaign.id,
                contact_id=contact.id,
                recipient_email=contact.email,
                recipient_name=contact.name,
                subject_line=email_content['subject'],
                email_body_html=email_content['html_body'],
                email_body_text=email_content['text_body'],
                personalization={'attachments': attachments} if attachments else None,
                status='queued'
            )
            self.db.add(outreach)
            generated_count += 1
        
        self.db.commit()
        
        print(f"[EmailDispatcher] Created campaign with {generated_count} emails")
        if attachments:
            print(f"[EmailDispatcher] Each email will include {len(attachments)} attachment(s)")
        return campaign.id
    
    def _check_limits(self) -> bool:
        """Check if we're within daily/hourly limits"""
        
        # Check daily limit
        today_start = datetime.now().replace(hour=0, minute=0, second=0)
        today_count = self.db.query(EmailOutreach).filter(
            EmailOutreach.status == 'sent',
            EmailOutreach.sent_at >= today_start
        ).count()
        
        if today_count >= self.daily_limit:
            return False
        
        # Check hourly limit
        hour_ago = datetime.now() - timedelta(hours=1)
        hour_count = self.db.query(EmailOutreach).filter(
            EmailOutreach.status == 'sent',
            EmailOutreach.sent_at >= hour_ago
        ).count()
        
        if hour_count >= self.hourly_limit:
            return False
        
        return True
