"""
Configuration management
"""
from pathlib import Path
from typing import Any, Dict

import yaml

_cache: Dict[str, Any] = {}

def load_config(filename: str) -> Dict[str, Any]:
    """Load YAML config file with caching"""
    if filename in _cache:
        return _cache[filename]

    config_path = Path(__file__).parent.parent / 'config' / filename
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    _cache[filename] = config
    return config

def get_keywords() -> Dict[str, Any]:
    """Get keywords configuration"""
    return load_config('keywords.yaml')

def get_budgets() -> Dict[str, Any]:
    """Get budgets configuration"""
    return load_config('budgets.yaml')

def get_profile() -> Dict[str, Any]:
    """Get user profile configuration"""
    return load_config('profile.yaml')

def matches_location(location: str) -> tuple[bool, str]:
    """
    Check if location matches Chennai or Remote (India)
    Returns: (matches, reason if not matched)
    """
    if not location:
        return False, "No location provided"

    keywords = get_keywords()
    location_lower = location.lower()

    # Check exclusions first
    for exclude in keywords['locations']['exclude_patterns']:
        if exclude.lower() in location_lower:
            return (False, f"Excluded: {exclude}")

    # Check Chennai
    for chennai in keywords['locations']['chennai']:
        if chennai.lower() in location_lower:
            return (True, "")

    # Check remote
    for remote in keywords['locations']['remote']:
        if remote.lower() in location_lower:
            return (True, "")

    return (False, "Not Chennai or Remote (India)")

def calculate_fit_score(job_title: str, job_text: str = "") -> int:
    """
    Calculate job fit score 0-100
    """
    if not job_title:
        return 0

    profile = get_profile()
    keywords = get_keywords()

    title_lower = job_title.lower()
    text_lower = (job_text or "").lower()
    combined = f"{title_lower} {text_lower}"

    score = 0

    # Primary keywords (5 points each, max 40)
    for keyword in keywords['keywords']['primary'][:8]:
        if keyword.lower() in combined:
            score += 5
            if score >= 40:
                break

    # Secondary keywords (2 points each, max 20)
    secondary_score = 0
    for keyword in keywords['keywords']['secondary'][:10]:
        if keyword.lower() in combined:
            secondary_score += 2
            if secondary_score >= 20:
                break
    score += secondary_score

    # User skills (3 points each, max 30)
    skill_score = 0
    for skill in profile['skills'][:10]:
        if skill.lower() in combined:
            skill_score += 3
            if skill_score >= 30:
                break
    score += skill_score

    # Check exclusions (-20 each)
    for exclusion in keywords['exclusions']:
        if exclusion.lower() in combined:
            score -= 20

    return max(0, min(100, score))

def select_resume_variant(job_title: str) -> str:
    """
    Select appropriate resume variant based on job title
    """
    profile = get_profile()
    title_lower = job_title.lower()

    mapping = profile.get('resume_mapping', {})
    for variant, keywords_list in mapping.items():
        for keyword in keywords_list:
            if keyword.lower() in title_lower:
                return profile['resume_variants'].get(variant,
                                                       profile['resume_variants']['default'])

    return profile['resume_variants']['default']
