"""
Job relevance checking - simple keyword-based approach
No LLM needed!
"""

def is_relevant_job(title: str, description: str) -> tuple[bool, float]:
    """
    Check if job is relevant for GenAI/LLM/AI Engineer role.
    Returns (is_relevant, confidence_score)

    Simple keyword matching approach - fast and free!
    """
    if not title and not description:
        return False, 0.0

    # Combine title and description for checking
    text = f"{title} {description}".lower()

    # HIGH PRIORITY KEYWORDS (strong signals)
    high_priority = [
        'genai', 'gen ai', 'generative ai',
        'llm', 'large language model',
        'ai engineer', 'ml engineer',
        'machine learning engineer',
        'deep learning engineer',
        'artificial intelligence engineer'
    ]

    # MEDIUM PRIORITY KEYWORDS (good signals)
    medium_priority = [
        'ai', 'artificial intelligence',
        'machine learning', 'ml',
        'deep learning', 'neural network',
        'nlp', 'natural language processing',
        'computer vision', 'cv',
        'pytorch', 'tensorflow', 'keras',
        'transformers', 'bert', 'gpt'
    ]

    # NEGATIVE KEYWORDS (likely not what we want)
    negative_keywords = [
        'data analyst', 'business analyst',
        'sales', 'marketing', 'customer success',
        'support engineer', 'qa engineer', 'test engineer',
        'devops engineer', 'sre', 'infrastructure',
        'frontend', 'full stack', 'web developer'
    ]

    score = 0.0

    # Check high priority keywords
    for keyword in high_priority:
        if keyword in text:
            score += 0.4

    # Check medium priority keywords
    for keyword in medium_priority:
        if keyword in text:
            score += 0.2

    # Check negative keywords (penalties)
    for keyword in negative_keywords:
        if keyword in text:
            score -= 0.3

    # Bonus for "engineer" in title
    if 'engineer' in title.lower():
        score += 0.1

    # Cap score between 0 and 1
    confidence = max(0.0, min(1.0, score))

    # Consider relevant if confidence >= 0.5
    is_relevant = confidence >= 0.5

    return is_relevant, confidence
