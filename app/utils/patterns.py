"""
Simple email pattern generation and inference
"""
import re
from typing import List


def generate_email_variations(name: str, domain: str) -> List[str]:
    """
    Generate common email patterns for a name
    
    Example:
        name = "Priya Sharma"
        domain = "infosys.com"
        
        Returns:
            ['priya.sharma@infosys.com', 'priyasharma@infosys.com', 
             'psharma@infosys.com', 'priya@infosys.com']
    
    Args:
        name: Full name (e.g., "Priya Sharma")
        domain: Email domain (e.g., "infosys.com")
    
    Returns:
        List of possible email variations
    """
    # Parse name
    parts = name.lower().strip().split()
    if len(parts) < 2:
        # Need at least first and last name
        return []
    
    # Clean parts (remove non-alphabetic characters)
    first = re.sub(r'[^a-z]', '', parts[0])
    last = re.sub(r'[^a-z]', '', parts[-1])
    
    if not first or not last:
        return []
    
    # Generate common patterns (in order of likelihood)
    patterns = [
        f"{first}.{last}@{domain}",     # priya.sharma@infosys.com (most common)
        f"{first}{last}@{domain}",      # priyasharma@infosys.com
        f"{first[0]}{last}@{domain}",   # psharma@infosys.com
        f"{first}@{domain}",            # priya@infosys.com
    ]
    
    return patterns


def save_inferred_contacts(names: List[str], domain: str, company_id: int, db) -> int:
    """
    Generate and save inferred email contacts to database
    
    Args:
        names: List of recruiter names
        domain: Company email domain
        company_id: Company ID
        db: Database session
    
    Returns:
        Number of contacts saved
    """
    from app.models.contact import Contact, Evidence
    
    saved = 0
    
    for name in names:
        # Generate email variations
        emails = generate_email_variations(name, domain)
        
        if not emails:
            continue
        
        # Use first variation (most common pattern: first.last@domain)
        email = emails[0]
        
        # Skip if already exists
        existing = db.query(Contact).filter(Contact.email == email).first()
        if existing:
            continue
        
        # Save as inferred contact
        contact = Contact(
            company_id=company_id,
            email=email,
            name=name,
            inferred=True,  # Mark as pattern-inferred
            status='discovered'
        )
        db.add(contact)
        db.flush()
        
        # Add evidence showing how it was generated
        evidence = Evidence(
            contact_id=contact.id,
            source_url='',
            source_type='pattern_inference',
            surrounding_text=f"Generated from name: {name}, pattern: first.last@{domain}"
        )
        db.add(evidence)
        saved += 1
        
        print(f"[Pattern] Inferred: {email} from {name}")
    
    db.commit()
    return saved


def extract_names_from_text(text: str) -> List[str]:
    """
    Extract potential recruiter names from text
    
    Looks for patterns like:
    - "Priya Sharma - Technical Recruiter"
    - "Posted by Rahul Verma"
    - "Contact: Anita Singh"
    
    Args:
        text: Text to extract names from
    
    Returns:
        List of names found
    """
    names = []
    
    # Pattern 1: Name followed by dash and title with recruiter keywords
    # "Priya Sharma - Technical Recruiter"
    pattern1 = r'\b([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]*)?)\s*[-–—]\s*[^,\n]*?(recruiter|talent|HR|hiring|people|acquisition)'
    matches1 = re.finditer(pattern1, text, re.IGNORECASE)
    for match in matches1:
        name = match.group(1).strip()
        names.append(name)
    
    # Pattern 2: "Posted by Name" or "Contact: Name"
    # "Posted by Rahul Verma, Senior..."
    pattern2 = r'(?:posted by|contact|by)\s*:?\s*([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]*)?)'
    matches2 = re.finditer(pattern2, text, re.IGNORECASE)
    for match in matches2:
        name = match.group(1).strip()
        # Verify name doesn't contain job title words
        if not any(word.lower() in name.lower() for word in ['posted', 'contact', 'by', 'the', 'and', 'join', 'team']):
            names.append(name)
    
    # Pattern 3: Name followed by comma and title with keywords
    # "Rahul Verma, Senior Talent Acquisition"
    pattern3 = r'\b([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]*)?)\s*,\s*[^,\n]*?(recruiter|talent|HR|hiring|people|acquisition)'
    matches3 = re.finditer(pattern3, text, re.IGNORECASE)
    for match in matches3:
        name = match.group(1).strip()
        names.append(name)
    
    # Pattern 4: Name in parentheses with title
    # "Contact (Anita Singh - HR Manager)"
    pattern4 = r'\(([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]*)?)\s*[-–—]'
    matches4 = re.finditer(pattern4, text, re.IGNORECASE)
    for match in matches4:
        name = match.group(1).strip()
        names.append(name)
    
    # Deduplicate and filter
    unique_names = []
    for name in names:
        # Must be 2-3 words
        parts = name.split()
        if 2 <= len(parts) <= 3:
            # Clean up
            name_clean = ' '.join(parts)
            if name_clean not in unique_names:
                unique_names.append(name_clean)
    
    return unique_names

