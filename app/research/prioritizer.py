"""
Contact prioritization logic
Priority: 1=highest (personal), 5=lowest (generic)
"""
from typing import Dict


def calculate_contact_priority(email: str, name: str = None, title: str = None, source_type: str = None) -> Dict[str, any]:
    """
    Calculate priority and classification for a contact
    
    Returns:
        {
            'priority': int (1-5),
            'email_type': str (personal, generic, inferred),
            'confidence': float (0.0-1.0)
        }
    """
    
    if not email or '@' not in email:
        return {'priority': 5, 'email_type': 'unknown', 'confidence': 0.1}
    
    local_part = email.split('@')[0].lower()
    
    # Priority 1: Personal emails (firstname.lastname or firstname)
    if '.' in local_part and len(local_part.split('.')) == 2:
        # Looks like firstname.lastname
        parts = local_part.split('.')
        if all(len(p) >= 2 for p in parts):  # Both parts at least 2 chars
            return {
                'priority': 1,
                'email_type': 'personal',
                'confidence': 0.9 if name else 0.7
            }
    
    # Check if name matches email pattern
    if name:
        name_lower = name.lower().replace(' ', '')
        if name_lower in local_part.replace('.', '').replace('_', ''):
            return {
                'priority': 1,
                'email_type': 'personal',
                'confidence': 0.95
            }
    
    # Priority 2: Named recruiter-specific emails
    recruiter_keywords = ['recruit', 'talent', 'hiring', 'hr']
    if any(kw in local_part for kw in recruiter_keywords):
        if name and title:
            return {
                'priority': 2,
                'email_type': 'personal',
                'confidence': 0.8
            }
        else:
            # Generic recruiter email
            return {
                'priority': 4,
                'email_type': 'generic',
                'confidence': 0.5
            }
    
    # Priority 3: Inferred emails (from pattern matching)
    if source_type == 'inferred':
        return {
            'priority': 3,
            'email_type': 'inferred',
            'confidence': 0.6
        }
    
    # Priority 5: Generic/fallback emails
    generic_prefixes = ['careers', 'jobs', 'hr', 'info', 'contact', 'hello', 'support', 'admin']
    if local_part in generic_prefixes:
        return {
            'priority': 5,
            'email_type': 'generic',
            'confidence': 0.9  # High confidence it's generic
        }
    
    # Default: Unknown pattern
    return {
        'priority': 4,
        'email_type': 'unknown',
        'confidence': 0.4
    }


def rank_contacts(contacts: list) -> list:
    """
    Rank contacts by priority and confidence
    Returns sorted list (best first)
    """
    return sorted(contacts, key=lambda c: (c.get('priority', 5), -c.get('confidence', 0)))
